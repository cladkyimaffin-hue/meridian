---
# === БАЗОВАЯ ИНФОРМАЦИЯ ===
date_created: 2026-08-30
date_modified: 2026-09-02
author: cladkyimaffin-hue
status: "completed"

# === КОНТЕКСТ СИСТЕМЫ ===
target_system: 'Windows Server 2022 (vmSAPP, 192.168.12.53), Workgroup'
environment: "production"

# === БЫСТРАЯ КЛАССИФИКАЦИЯ ===
category: "documentation"
severity: "info"
problem: |
  Необходима централизованная навигация по базе знаний настройки RemoteApp для быстрого поиска решений и контекста без ручного перебора файлов.
solution: |
  Создан индексный файл (INDEX.md), связывающий все документы по RemoteApp в единую структуру с тегами, кратким описанием и AI-полями.
root_cause: |
  Отсутствие единой точки входа замедляет поиск специфичных решений (например, по перенаправлению принтеров или лимитам сессий).

# === AI-СПЕЦИФИЧНЫЕ ПОЛЯ ===
ai_summary: |
  Индекс папки RemoteAPP. Содержит ссылки на 3 файла: базовая настройка RemoteApp через RDP Wrapper в рабочей группе, публикация приложений и отключение перенаправления клиентских принтеров.
key_takeaways:
  - 'Используется упрощённый метод RemoteApp + RDP Wrapper (форк sebaxakerhtc) для обхода лимита в 2 сессии в Workgroup'
  - 'Критичные параметры реестра: fDisabledAllowList=1 и fAllowUnlistedRemotePrograms=1'
  - 'Для отключения проброса принтеров используется fDisableCpm=1 в политиках и redirectprinters:i:0 в RDP-файле'
dont_repeat:
  - 'Не предлагать развёртывание полноценной роли RDS с Connection Broker — сервер в рабочей группе (Workgroup)'
  - 'Не предлагать использование оригинального RDP Wrapper (stascorp) — он заброшен и не поддерживает Server 2022'
assumptions:
  - 'Сервер находится в рабочей группе (Workgroup), без Active Directory'
  - 'Целевое приложение: Lvision (C:\LVision\LVMain.exe)'

# === СВЯЗИ ===
related_files:
  - "Настройка RemoteApp на Windows Server 2022 #1.md"
  - "Настройка RemoteApp на Windows Server 2022 #2.md"
  - "Отключение перенаправления принтеров.md"
tags:
  - "RemoteApp"
  - "Windows-Server-2022"
  - "RDP-Wrapper"
  - "Workgroup"

# === ВРЕМЕННОЙ КОНТЕКСТ ===
last_incident: 2026-08-30
next_review: 2027-08-30
valid_until: 2028-08-30

# === ОТВЕТСТВЕННОСТЬ ===
reviewer: ""
approval_status: "approved"
---

# 📁 Индекс папки: RemoteAPP (Windows Server 2022)

**Описание:** База знаний по развертыванию и настройке служб удаленных рабочих столов (RemoteApp) на Windows Server 2022 в рабочей группе (Workgroup) с использованием RDP Wrapper для снятия лимита сессий.

## 📄 Список файлов и их назначение

1. [Настройка RemoteApp на Windows Server 2022 #1.md](./Настройка%20RemoteApp%20на%20Windows%20Server%202022%20%231.md)
   - **Краткое содержание:** Базовая установка и настройка RemoteApp без полноценной роли RDS.
   - **Ключевые этапы:** Установка RDP Wrapper (форк sebaxakerhtc) для обхода лимита в 2 сессии, настройка реестра (`fDisabledAllowList`, `fAllowUnlistedRemotePrograms`), права NTFS на папку приложения, создание эталонного RDP-файла (`alternate shell:s:rdpinit.exe`).

2. [Настройка RemoteApp на Windows Server 2022 #2.md](./Настройка%20RemoteApp%20на%20Windows%20Server%202022%20%232.md)
   - **Краткое содержание:** Публикация приложений, настройка безопасности и сертификатов.
   - **Ключевые этапы:** Публикация конкретных приложений (Lvision), настройка SSL-сертификатов, конфигурация Remote Desktop Gateway, правила брандмауэра и финальное тестирование подключений.

3. [Отключение перенаправления принтеров.md](./Отключение%20перенаправления%20принтеров.md)
   - **Краткое содержание:** Решение проблемы дублирования и проброса локальных принтеров клиентов в сессию RemoteApp.
   - **Ключевые этапы:** Добавление `redirectprinters:i:0` в клиентский RDP-файл и установка серверного параметра реестра `fDisableCpm = 1` в `HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services` с перезапуском TermService.

## 🏷️ Ключевые темы (теги для поиска)
`Windows Server 2022` | `RemoteApp` | `RDP-Wrapper` | `Workgroup` | `Lvision` | `Printer-Redirection` | `RDP-File`
