# Карта данных базы LV_MERIDIAN (WMS, MSSQL 2019)

Дата снятия: **2026-11-25**, сервер `wmsDB` (192.168.12.153), доступ `grafana_ro` (read-only).
Методика: системные каталоги `sys.objects / sys.columns / sys.foreign_keys / sys.indexes` + подсчёт строк через `sys.partitions` (прямой `sys.dm_db_partition_stats` запрещён правами).
Машиночитаемые приложения: [`live-tables.csv`](../datamap/live-tables.csv) (505 таблиц с колонками), [`all-tables.csv`](../datamap/all-tables.csv) (все 1 238).

Связанные документы: исходные требования к интеграции и настройке WMS — [`integration-1c/`](integration-1c/README.md); состояние и витрины Superset — [`AI-CONTEXT.md`](AI-CONTEXT.md), история работ — [`JOURNAL.md`](JOURNAL.md).

## 1. Общая картина

| Показатель | Значение |
|---|---|
| Таблиц | **1 238** (из них с данными — **505**, пустых — **733**) |
| Представлений (VIEW) | **1 306** — все с сохранённым определением, самое длинное 10 347 символов |
| Хранимых процедур / функций | 131 / 85 |
| Внешних ключей (FK) | **2 076** |
| Таблиц с первичным ключом | 1 153, **85 без PK** |
| Колонок | ~34 700, из них int — 19 521, varchar — 7 617, numeric — 3 197, nvarchar — 2 726, datetime — 1 115 |
| Схема | одна: `dbo` |
| Логический сайт | один: `001 «Москва»` (`COM_LogisticSite`) |
| Языки описаний | `msg_languageID=1` (англ., 5 884 строки) и `=4` (рус., 4 317) |
| Окно данных | приходы с 2025-10-29, заказы с 2026-02-17, журнал операций `LV_Log` по 2026-11-24 |

Важно: база **не «толстая»**. Живых строк мало (остатки — 399, заказы — 189, приходы — 298, задачи — 730), но справочники полные (15 473 товара, 14 390 клиентов, 14 470 компаний, 14 183 поставщика). Это похоже на рабочую базу с историей, где операционные документы «прокручиваются», а справочники живут постоянно.

## 2. Модули по префиксам

| Префикс | Таблиц (всего / с данными) | Что это (проверено по содержимому) |
|---|---|---|
| `LV_` | 577 / 229 | **Ядро WMS** LogisVision: товары, остатки, приходы, заказы, задачи, локации, атрибуты |
| `SYS_` | 180 / 176 | Системные справочники-перечисления (`SYS_ItemType`, `SYS_HazardType`, `SYS_ContainerTransitReason`…). Почти все живые, но по 2–6 строк |
| `COM_` | 75 / 36 | Общие сущности платформы: `COM_LogisticSite`, `COM_Employee`, `COM_Person`, `COM_Attachment`, `COM_Dashboard`, `COM_Inventory`, `COM_Variant` |
| `BI_` | 38 / 17 | Встроенный BI-модуль: прайс-листы, замеры, тарифы, `BI_OPERATION_LOG` |
| `CT_` | 42 / 8 | Контейнеры/карго-перевозки (`CT_CargoOrder`, `CT_CargoReceipt`, `CT_Container`) |
| `GT_` | 32 / 1 | Книга проходов/терминала (gate) — практически не используется |
| `ST_` | 68 / 2 | Финансовые документы и транзакции (`ST_DocumentTrans`, `ST_FinancialYear`) |
| `RTD_` | 44 / 3 | Real-time данные с ТСД (радиотерминалов) |
| `PRO_` | 16 / 3 | Производственный модуль |
| `FSM_` | 79 / 0 | Пищевая безопасность/прослеживаемость — **полностью пусто** |
| `ANT_` | 22 / 15 | Интеграции: `ANT_ExportOrder*`, `ANT_KM_*` (маркировка «Честный знак»), `ANT_AutoPrintReport*` |
| `STGR_` | 19 / 0 | Группы хранения — пусто |
| `LOG_` | 4 / 4 | Наследие: `LOG_Order`, `LOG_OrderShipItem`, `LOG_OrderShipment`, `LOG_Receipt` (снимки для 1С) |
| `TIM_` | 2 / 2 | Замороженные паллеты/локации (`TIM_FROZEN_STOCK_*`) |

Вывод: **для отчётов нужны `LV_` + часть `COM_` + `ANT_` + `LOG_`**, остальное — служебные перечисления, их трогать незачем.

## 3. Поток данных WMS (как устроен бизнес-процесс)

```
Приход: LV_Receipt → LV_ReceiptItem → LV_ReceiptItemAllocation
        ↓ размещение (putaway)
Хранение: LV_Stock (остаток: товар × локация × контейнер)
        ↑ перемещения/задачи
LV_Task (задание: откуда → куда, кто, когда)  ← LV_TaskList, LV_TaskSequence
        ↓ отбор/сборка
Расход: LV_Order → LV_OrderItem → LV_OrderShipItem
        → LV_OrderShipment (партия отгрузки) → LV_OrderShipItemStock
Журнал: LV_Log (заголовок операции) + LV_LogStock (движение товара)
        + LV_LogStockContainer (движение контейнера/SSCC)
Инвентаризация: LV_Count → LV_CountDetailStock → LV_CountStockDif
```

`LV_Task` — центральная таблица операций: 28 связей, содержит `tsk_FromLocationID/tsk_ToLocationID`, `tsk_ExpUserID/tsk_ActualUserID` (исполнитель), `tsk_CreateTime/tsk_ActualTime` (план/факт), `tsk_StatusID` → `LV_ProgressStatus`.

## 4. Ключевые таблицы (проверено по колонкам и связям)

### Товар
- **`LV_Product`** (15 473) — 45 колонок: `prd_ID`, `prd_PrimaryCode` (артикул, формат `ER-00132216`), `prd_TemplateID` → `LV_ProductTemplate`, `prd_ItemTypeID` → `SYS_ItemType`, `prd_LotControlledLED`, `prd_OriginCountryID`, `prd_ProducerCompanyID`.
- **`LV_ProductLang`** (30 946) — названия: `prdl_ProductID`, `prdl_Description`, `prdl_ShortDescription`, `prdl_LanguageID` (4 = русский).
- **`LV_ItemUnit`** (15 475) — 29 колонок, **100 связей**: единицы измерения товара (`itu_ProductID`, `itu_UnitID`, `itu_UseLevelID`, признаки `itu_OrderUnitLED`, `itu_ReceivingUnitLED`, `itu_PickWholeLED`).
- **`LV_ProductAttributesValues`** (112 127) — самая большая: `pav_ProductID`, `pav_attributeID` → `LV_ProductAttributes`, `pav_Value`. EAV-атрибуты товара.
- **`LV_ProductStockAttributes`** (32 010) — складские атрибуты товара (партии, сроки годности — уточнить по `LV_StockAttributes`).
- **`LV_ProductBarcode`** (3 680), **`LV_ProductDepositor`** (15 473 — товар↔поклажедатель), **`LV_ProductLS`** (15 473).

### Остатки
- **`LV_Stock`** (399) — `stk_LocationID` → `LV_Location`, `stk_ProductID` → `LV_Product`, `stk_DepositorID` → `LV_Depositor`, `stk_ContainerID` → `LV_StockContainer`, `stk_CUItemUnitID` → `LV_ItemUnit`, `stk_CUQuantity` (всего) / `stk_CUQuantityFree` (свободно). Разница = резерв. Плюс `stk_ReserveReasonID` → `LV_StockReserveReason`, `stk_UnsuitReasonID` → `LV_UnsuitabilityReason`.
- **`LV_StockContainer`** (255) — контейнеры: `stc_SSCC`, дата входа.
- **`LV_StockAttributesValues`** (887) / **`LV_ShipStock`** (267) — атрибуты и «отгружаемый» остаток.
- Фактические цифры: **217 товаров, 250 локаций, 202 контейнера** в остатках.

### Локации
- **`LV_Location`** (2 938, 66 колонок) — `loc_Code`, координаты (`loc_Level`, `loc_Column`, `loc_Side`…), признаки назначения (`loc_PickingLED`, `loc_ReceivingLED`, `loc_Shipping`→`loc_SendingLED`, `loc_DamagedLED`, `loc_ReplenishSourceLED`), `loc_DepositorID`, `loc_CapacityStatusID`.
- **`LV_Zone`** (15) — зоны: `IN` Приемка, `OUT` Отгрузка, `BUF` Буфер, `A`/`B` Хранение A/B, `C` Готовые заказы, `E`/`F` Проверка ЧЗ, `X` Комплектация, `Y` ОТК, `BRAK` Брак, `OBR` Образцы, `VIRT` Виртуальная, `OFF` Офис, `S4` Склад 4.
- **`LV_LocZone`** (2 933) — связь локация↔зона (у локации может быть несколько зон).

### Документы
- **`LV_Receipt`** (298) — `rct_Code`, `rct_InputDate/ExpectedDate/ActualDate`, `rct_SupplierID`, `rct_TypeID` → `LV_ReceiptType`, `rct_ProgressID` → `LV_ProgressStatus`, `rct_LineCount`, веса/объёмы.
- **`LV_Order`** (189) — `ord_Code`, `ord_CustomerID`, `ord_TypeID` → `LV_OrderType`, `ord_StatusID` → `LV_OrderStatus`, `ord_InputDate`, `ord_ExpShipDate`, `ord_LineCount`.
- **`LV_OrderShipment`** (190) — партии: `ost_OrderID`, `ost_StatusID` → `LV_OrderStatus`, `ost_ShipDate`, `ost_CompleteDate`, `ost_DelayReasonID`, `ost_NoDeliveryReasonID`.
- **`LV_ReceiptItem`** (594) / **`LV_OrderItem`** (370) / **`LV_OrderShipItem`** (381) — строки.

### Журнал операций
- **`LV_Log`** (4 394) — `log_DateTime`, `log_UserID`, `log_SessionID`, `log_TransactionTypeID` → `LV_TransactionType`, ссылки на документы, `log_TotalDuration`, `log_UserDuration`.
- **`LV_LogStock`** (8 828) — движение товара: `lsk_LogID` → `LV_Log.log_ID`, `lsk_ProductID`, `lsk_FromLocationID`/`lsk_LocationID`, `lsk_FromStockID`/`lsk_ToStockID`, `lsk_CUQuantity`.
- **`LV_LogStockContainer`** (8 834) — движение контейнера: `lsc_LogID`, `Lsc_SSCC`, `Lsc_LocationID`, `Lsc_ReceiptID`.
- ⚠️ У этих трёх таблиц **нет внешних ключей** (0 связей) — связи только логические, по `lsk_LogID = log_ID` и т. п.

### Люди и доступ
- **`LV_Users`** (8) — учётки WMS: `usr_Login`, `usr_PersonID` → `COM_Person`, `usr_LanguageID`, `usr_UserTypeID`.
- **`COM_Employee`** (8) — сотрудники склада: на них ссылаются `LV_Task` (план/факт), `LV_Count`, `LV_Session` … **учтите: сотрудников всего 8**.
- **`LV_Session`** (2 134) — сессии ТСД: `ses_UserID`, `ses_HostID`, `ses_StartTime/EndTime`, `ses_ClarkID`.

## 5. Словари и локализация

- **`LV_Messages`** (10 201) — тексты/статусы: `msg_code` (напр. `ORD_Complete`) + `msg_Greek` («Выполнен») + `msg_languageID`. Правильный шаблон подписи статуса: `ISNULL(m.msg_Greek, s.ors_MessageCode)` при `msg_languageID=4`.
- Статусы заказа `LV_OrderStatus`: `ORD_ToProcess`, `ORD_ToPick`, `ORD_InPicking`, `ORD_Picked`, `ORD_InSorting`, `ORD_Sorted`, `ORD_InPacking`, `ORD_Packed`, `ORD_InLoading`, `ORD_Complete`, `ORD_Canceled`, `ORD_SoftAllocation`, `ORD_HardAllocation`, `ORD_Suspended`, `ORD_Checked`, `ORD_InChecking` (16).
- Статусы задач `LV_ProgressStatus`: `Status_Pending`, `Status_Executing`, `Status_Done`, `Status_Cancelled`, `Status_Suspended`, `Status_Incomplete` (6).
- 37 таблиц `*Lang` — переводы справочников; для русского брать `LanguageID=4`.
- Единицы: `LV_Unit` (28) + `LV_UnitLang`, связка с товаром через `LV_ItemUnit`.

## 6. Слой представлений (1 306)

Именование: `V_` (800), `VST_` (133), `VP_` (124), `VBO_` (48), `VBI_` (43), `VCT_` (40), `VGT_` (36), `v_` (20), `view_` (15), `VPL_` (15), `VW_` (10).

Это, по сути, готовая «витрина» вендора: `V_…` повторяют базовые таблицы с расшифровками (названия вместо ID), `VST_` — складские, `VP_` — производственные, `VBO_`/`VBI_` — биллинг/BI. Практический вывод: **прежде чем писать JOIN с `*Lang` и `LV_Messages`, стоит проверить, нет ли готового `V_`** — сэкономит половину запроса. Проверять так:

```sql
SELECT TOP 5 * FROM dbo.V_Stock;
SELECT name, LEN(CAST(definition AS nvarchar(max))) FROM sys.sql_modules m
JOIN sys.objects o ON o.object_id=m.object_id WHERE o.name='V_Stock';
```

## 7. Обмен с 1С и маркировка

- **`LV_ImpLogFile`** (43 789) → **`LV_ImpLogRecord`** (54 618): журнал импорта файлов, `ilr_SuccessLED`, `ilr_InsertedRecords`, `ilr_failedRecords`, `ilr_LogMessage`.
- **`LV_ImportIntItem`** (407) / **`LV_ImportExtItem`** (232) / **`LV_ImportFile`** (12) / **`LV_ImportStatus`** (12) — очередь и статусы обмена.
- **`ANT_ExportOrder`** (91), **`ANT_ExportReceipt`** (212), **`ANT_ExportOrderChangeStatus`** (379), **`ANT_ExportOrderKM`** (19), **`ANT_ExportReceiptKM`** (85), **`ANT_KM_ImportPost1`** (1 839), **`a_Tab_KM`** (671) — выгрузка в 1С и «Честный знак».
- Устаревшие снимки: `LOG_Order` (735), `LOG_OrderShipItem` (1 812), `LOG_OrderShipment` (1 094), `LOG_Receipt` (802) — использовались прошлым интегратором; для новых отчётов лучше `LV_*`.

## 8. Рецепты соединений (проверены по FK)

```sql
-- Остатки с названием товара, зоной и единицей
SELECT l.loc_Code, z.zon_Description, p.prd_PrimaryCode, pl.prdl_Description,
       ul.untl_Description, s.stk_CUQuantity, s.stk_CUQuantityFree
FROM dbo.LV_Stock s
JOIN dbo.LV_Location l      ON l.loc_ID = s.stk_LocationID
LEFT JOIN dbo.LV_LocZone lz ON lz.lzn_LocationID = l.loc_ID
LEFT JOIN dbo.LV_Zone z     ON z.zon_ID = lz.lzn_ZoneID
JOIN dbo.LV_Product p       ON p.prd_ID = s.stk_ProductID
LEFT JOIN dbo.LV_ProductLang pl ON pl.prdl_ProductID = p.prd_ID AND pl.prdl_LanguageID = 4
LEFT JOIN dbo.LV_ItemUnit iu ON iu.itu_ID = s.stk_CUItemUnitID
LEFT JOIN dbo.LV_Unit u     ON u.unt_ID = iu.itu_UnitID
LEFT JOIN dbo.LV_UnitLang ul ON ul.untl_UnitID = u.unt_ID AND ul.untl_LanguageID = 4;

-- Движение товара по дням (журнал)
SELECT CAST(g.log_DateTime AS date) AS day, p.prd_PrimaryCode,
       SUM(ls.lsk_CUQuantity) AS qty
FROM dbo.LV_LogStock ls
JOIN dbo.LV_Log g ON g.log_ID = ls.lsk_LogID
JOIN dbo.LV_Product p ON p.prd_ID = ls.lsk_ProductID
GROUP BY CAST(g.log_DateTime AS date), p.prd_PrimaryCode;

-- Отгрузки: заказ → партия → статус
SELECT o.ord_Code, sh.ost_Code, o.ord_InputDate, sh.ost_ShipDate,
       ISNULL(m.msg_Greek, st.ors_MessageCode) AS status_ru
FROM dbo.LV_Order o
JOIN dbo.LV_OrderShipment sh ON sh.ost_OrderID = o.ord_ID
LEFT JOIN dbo.LV_OrderStatus st ON st.ors_ID = sh.ost_StatusID
LEFT JOIN dbo.LV_Messages m ON m.msg_code = st.ors_MessageCode AND m.msg_languageID = 4;
```

## 9. Ловушки (проверено на практике)

1. **Коллации.** База `Latin1_General_CI_AS_KS_WS`, а часть колонок — `Cyrillic_General_CI_AS`. Любой `+`/`UNION` строк из разных таблиц падает с ошибкой 451. Лечится `COLLATE Cyrillic_General_CI_AS` (или `DATABASE_DEFAULT`) на строковом выражении.
2. **Права.** `grafana_ro` — не sysadmin: `sys.dm_db_partition_stats`, `sys.dm_db_index_usage_stats`, `VIEW SERVER STATE` **запрещены**. Строки считать через `sys.partitions` + `sys.allocation_units`. Для «когда последний раз писали» нужен другой подход (например, `MAX(дата)` в самой таблице).
3. **Нет FK у журналов** (`LV_Log`, `LV_LogStock`, `LV_LogStockContainer`, `LV_LogStockPackType`) — СУБД не защитит от «висячих» ссылок, а планы запросов хуже.
4. **85 таблиц без PK** — прежде чем строить по ним дашборд, проверить уникальность ключа.
5. **733 пустые таблицы** — не пугаться «маленьких» цифр в отчётах: данные просто в других таблицах.
6. **Сотрудников 8, пользователей 8** — «нагрузка по исполнителям» будет считаться по горстке людей, это нормально для этой базы.

## 10. Что делать дальше (план отчётов)

1. **Витрина «Остатки»** — `LV_Stock` + локации + зоны + товар + единица (готовый SQL выше). В Superset: dataset + дашборд «Остатки: сводка / по зонам / по товарам». ✅ сделано 2026-11-25 (`dm_stock`, `wms-stock-parallel`).
2. **Витрина «Движение»** — `LV_Log` + `LV_LogStock` по дням, типам операций (`LV_TransactionType`), зонам. ✅ сделано 2026-11-26 (`dm_movement`, `wms-movement`).
3. **Витрина «Приходы»** — `LV_Receipt` + `LV_ReceiptItem` + поставщик + статус. ✅ сделано 2026-11-26 (`dm_receipts`, `dm_receipt_lines`, `wms-receipts`).
4. **Витрина «Расход»** — `LV_Order` + `LV_OrderShipment` + `LV_OrderShipItem` + клиент + статус. ✅ сделано 2026-11-26 (`dm_orders`, `dm_order_lines`, `wms-orders`).
5. **Витрина «Задачи/исполнители»** — `LV_Task` + `COM_Employee` + `LV_ProgressStatus`. ⏳ следующее.
6. **Витрина «Обмен с 1С»** — `LV_ImpLog*` + `LV_ImportStatus` (ошибки импорта). ⏳ следующее.

Сверка кодов типов прихода/расхода и статусов с ТЗ — [TYPE-CODES-CHECK.md](TYPE-CODES-CHECK.md): коды совпадают полностью.

Порядок: сначала 1 и 2 (самые востребованные), затем 3–4, потом 5–6. Каждая витрина = один SQL-датасет в Superset, поверх — дашборд с фильтрами по зоне/товару/дате.

Состояние Superset, первая витрина `dm_stock` и починка прав (проверенные цифры) — в [`AI-CONTEXT.md`](AI-CONTEXT.md), раздел «Superset»; хронология — в [`JOURNAL.md`](JOURNAL.md).
