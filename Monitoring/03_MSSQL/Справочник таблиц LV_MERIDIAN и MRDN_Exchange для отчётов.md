---
document_id: MONITORING-MSSQL-LV-MERIDIAN-TABLES-2026-001
title: "Справочник таблиц LV_MERIDIAN и MRDN_Exchange для отчётов"
document_type: reference
status: in_progress
priority: high
date_created: 2026-11-21
date_modified: 2026-11-21
next_review: 2026-12-21
author: "Claude (по запросу cladkyimaffin-hue)"
category: 03_MSSQL
tags:
  - Monitoring
  - MS-SQL
  - Grafana
ai_summary: "Карта таблиц баз WMS на wmsDB для складских отчётов: LV_MERIDIAN (504 таблицы с данными из 1238, малые объёмы) и MRDN_Exchange (30 таблиц IFC_*, обмен с 1С). Таблицы сгруппированы по темам (товар, остатки и места, приход, заказы, задания, журналы, обмен) с числом строк. Внешних ключей нет, связи подтверждены данными (LV_LogStock → LV_Log, IFC_Import* ↔ LV_Receipt). Данные за декабрь 2025 — ноябрь 2026, база в пилоте (последняя операция журнала 2026-11-05). Часть таблиц ещё не читалась."
dont_repeat:
  - "Названия типов операций в LV_TransactionType хранятся как английские ключи сообщений (trt_MessageCode), русских подписей в этой таблице нет. Русские названия в отчётах берутся из словаря сообщений LV_Messages (есть русский и английский варианты); перевод по смыслу без словаря — INFERRED."
  - "2938 — это число всех ячеек всех зон (LV_Location), а не число ячеек одной зоны. Зон в LV_Zone 15, «Хранение А» — одна из них."
  - "Внешних ключей нет, поэтому связи берутся по именам столбцов и проверяются на данных (число «сирот»). Соединение таблиц двух баз требует COLLATE DATABASE_DEFAULT в условии."
  - "Данные малые: самая большая таблица около 112 тыс. строк, нагрузка на боевую базу от отчётов невелика. Но база в пилоте: после запуска 1С ERP объёмы вырастут, цифры в этом справочнике на 2026-11-17."
  - "Смысл «вход» и «выход» в именах IFC_Import* и IFC_Export* — с точки зрения WMS: Import пишет внешняя система (1С), Export пишет WMS. Необработанные записи в IFC_ExchangeQueueExport до запуска 1С ERP не ошибка обмена."
  - "IFC_ImportProduct (16 941) больше LV_Product (15 473): справочник товара, скорее всего, приходит из 1С (INFERRED); сопоставление ключей не проверялось, разницу в числе строк не считать ошибкой без разбора."
related_files:
  - MONITORING-MSSQL-LV-MERIDIAN-DATASOURCE-2026-001
schema_version: "1.1"
environment: production
hostname: wmsDB
last_verified: 2026-11-18
---

# Справочник таблиц LV_MERIDIAN и MRDN_Exchange для отчётов

## Что описывает документ

Карта таблиц WMS, нужных для складских отчётов Grafana: что где лежит, сколько строк, как таблицы связаны. Доступ к базам — `MONITORING-MSSQL-LV-MERIDIAN-DATASOURCE-2026-001`. Всё ниже получено чтением схемы и агрегатами (`COUNT`, `MIN`, `MAX`), значения товаров и людей не выводились. Числа — на 2026-11-17–2026-11-18. Обмену с 1С и данным для разбора ошибок — отдельный документ находок (следующий шаг работ).

## Базы и объёмы (VERIFIED)

- `LV_MERIDIAN`: 1238 таблиц, из них 504 с данными и 734 пустые. Самая большая — `dbo.LV_ProductAttributesValues`, около 112 тыс. строк.
- `MRDN_Exchange`: 30 таблиц `IFC_*`, 31 процедура, представлений нет. В базах нет внешних ключей (связи — по именам столбцов).
- Данные журнала за около 11 месяцев: с 2025-12-04 по 2026-11-05. За последние 30 дней около 52 записей журнала, за 7 дней — ни одной; последнее выполненное задание — 2026-10-28; новые приходы в `LV_Receipt` ещё заводятся (6 за неделю). `LV_Log` и `LV_Task` начинаются в одну секунду (2025-12-04 11:04:17): похоже на первичную загрузку (INFERRED).

## Карта таблиц `LV_MERIDIAN` (число строк в скобках, если измерялось)

| Тема | Таблицы |
|---|---|
| Товар | `LV_Product` (15 473 строки, 45 столбцов), `LV_ProductLS`, `LV_ProductLang`, `LV_ProductBarcode`, `LV_ProductDepositor`, `LV_ItemUnit`, `LV_ItemPackType`, `LV_ProductStockAttributes` |
| Остатки и места | `LV_Stock` (397), `LV_StockContainer` (251), `LV_Location` (2938 ячеек, 66 столбцов), `LV_LocZone`, `LV_Zone` (15 зон) |
| Приход | `LV_Receipt` (298), `LV_ReceiptItem` (594), `LOG_Receipt` |
| Расходные заказы | `LV_Order` (189), `LV_OrderItem` (370), `LV_OrderShipment` (190 партий, 381 позиция), `LV_OrderShipItem`, `LV_OrderStatus` |
| Задания и перемещения | `LV_Task` (728, 38 столбцов), `LV_TaskList`, `LV_TaskPackType`, `LV_ProgressStatus` (6 статусов) |
| Журналы движения | `LV_LogStock` (8822), `LV_LogStockContainer`, `LV_Log` (4388), `LV_LocTransactionType`, `LV_TransactionType` (31 тип операции), словарь `LV_Messages` |

Роль каждой группы выведена по именам и спецификации и подтверждена данными там, где ниже стоит VERIFIED; остальное INFERRED.

## Подтверждённые связи и справочники (VERIFIED)

- `LV_LogStock` → `LV_Log` по `lsk_LogID`: все 8822 строки имеют пару, «сирот» нет. В журнале движения 278 товаров и 341 ячейка; активность по месяцам: апрель 249, май 1506, июнь 3201, июль 1255, август 583, сентябрь 1144, октябрь 474 строк.
- `LV_Task`: три типа — Picking 387, Putting 268, Relocate 69 (всего 728); почти все в статусе Done, незавершённых 4. Статусы `LV_ProgressStatus`: Pending, Executing, Done, Cancelled, Suspended, Incomplete.
- Расходные партии: статус `ost_StatusID` → `LV_OrderStatus`: «Выполнен» 94, «Отобран» 31, «Отменён» 27, «Приостановлен» 14, «В процессе» 14, «Упаковка» 4, «Загружается» 3, «Отбор» 3 (итого 190). По спецификации «расходная партия» — `LV_OrderShipment` (INFERRED); у каждого заказа есть хотя бы одна партия.
- Приход: тип в `rct_TypeID`, семь типов, 30 приходов без типа; расшифровка `LV_ReceiptType` не читалась.
- Сверка прихода с обменом: `IFC_ImportReceiptHeader.ReceiptCode` и `IFC_ExportReceiptHeader.ReceiptCode` ↔ `LV_Receipt.rct_Code`; строки `IFC_ImportReceiptDetails` связаны с заголовком по `ReceiptID` = `ID` (0 «сирот» из 478). Соединение двух баз — с `COLLATE DATABASE_DEFAULT`.

## Таблицы `MRDN_Exchange` (обмен с 1С)

Обмен именно с 1С: в `IFC_UnitMapping` (5 строк) есть столбец `UnitCode1C` — соответствие единиц измерения 1С и WMS (VERIFIED).

| Группа | Таблицы (строк) |
|---|---|
| Очереди обмена | `IFC_ExchangeQueueImport` (32 769), `IFC_ExchangeQueueExport` (370), `IFC_ExchangeQueueType` (17) |
| Вход: справочники | `IFC_ImportProduct` (16 941), `IFC_ImportSupplier` (62), `IFC_ImportCustomer` (66), `IFC_ImportAgency` (86) |
| Вход: приход | `IFC_ImportReceiptHeader` (272), `IFC_ImportReceiptDetails` (478), `IFC_ImportReceiptDocumentStatus` (6) |
| Вход: заказы | `IFC_ImportOrderHeader` (63), `IFC_ImportOrderDetails` (141), `IFC_ImportOrderChange` (66) |
| Выход: приход и заказы | `IFC_ExportReceiptHeader` и `IFC_ExportReceiptDetails`, `IFC_ExportOrderHeader` и `IFC_ExportOrderDetails`, `IFC_ExportOrderChangeStatus` (115), `IFC_ExportOrderCancel` |
| Прочее | `IFC_UnitMapping` (5), `sysdiagrams` (0) |

Разбор очереди по типам и ошибкам — в отдельном документе находок, чтобы не дублировать.

## Не проверено

- Расшифровка типов прихода и заказа (`LV_ReceiptType`, `LV_OrderType`), 30 приходов без типа.
- Сверка `IFC_Import*` с `LV_*` полностью; сопоставление ключей `IFC_ImportProduct` и `LV_Product`.
- Причина расхождения статусов прихода и заказа с спецификацией обмена; около 85 % спецификации обмена с 1С не читалась.
- Русские подписи типов операций из `LV_Messages` в справочник не вносились.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере: каждый пункт — реальная преграда или наблюдение этой работы.

## Связанные документы
- `MONITORING-MSSQL-LV-MERIDIAN-DATASOURCE-2026-001` — источник данных, права читающего логина.

---
*Создан 2026-11-21 по чатам «Поиск таблиц товаров в LV_MERIDIAN» и «Проверка актуальности документа по загрузкам» (2026-11-17 — 2026-11-20). Секреты, данные товаров и людей и имена учётных записей не включены.*
