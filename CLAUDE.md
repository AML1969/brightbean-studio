# BrightBean Studio — заметки для Claude Code

Форк github.com/brightbeanxyz/brightbean-studio (upstream как remote `upstream`). Документы владельца:
`docs/ЗАПУСК.md` (как запустить), `docs/АНАЛИЗ.md` (архитектура и риски), `docs/ПЛАН.md` (дорожная карта).

## Команды
- Запуск: `python manage.py runserver` + `python manage.py run_studio_worker` (не `process_tasks`). В Docker: `docker compose up -d --build`.
- Тесты требуют PostgreSQL 16, на SQLite не идут. Нативно: `DJANGO_SETTINGS_MODULE=config.settings.test SECRET_KEY=x DATABASE_URL=postgres://postgres:postgres@localhost:5432/brightbean_test pytest -q` (~2 мин, 2736 тестов). В Docker: `docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test -e DB_HOST=postgres app pytest -q`.
- Перед коммитом: `make check` (ruff check, ruff format --check, mypy, makemigrations --check), как в `.github/workflows/ci.yml`.
- Tailwind: `cd theme/static_src && npm run build` (dist гитигнорен; в Docker собирает сервис `tailwind`).
- Проверка, что воркер получил задачи: в `/admin/background_task/task/` есть `run_publish_cycle`, `confirm_pending_publishes`, `run_inbox_sync_cycle`, `sync_all_account_analytics`.

## Правила
- Ядро (`apps/publisher/engine.py`, `providers/`) менять только с тестами; оно защищает от двойной публикации.
- Новая платформа затрагивает ~16 файлов и 2 миграции (образец: коммит `e4da3a2`, DEV.to): `providers/<x>.py`, `providers/__init__.py`, `PlatformCredential.Platform` + миграции `credentials` и `social_accounts` (три модели), `SocialAccount.PLATFORM_CHAR_LIMITS/PLATFORM_FIELD_CONFIG/platform_icon`, `apps/api/limits.py`, `apps/analytics` (`NO_ANALYTICS_PLATFORMS` + `BACKFILL_DAYS_PER_PLATFORM=0`, если аналитики нет), `apps/common/context_processors.py`, connect-view + URL + шаблон, иконки в двух `_platform_icon.html`, ветка в `_resolve_publish_credentials` (engine.py) для per-account данных, и жёсткий набор в `tests/providers/test_base.py`.
- Исправления, полезные upstream (баги, тесты), оформлять отдельными небольшими коммитами, чтобы предложить PR-ом.
- Интерфейс остаётся на английском (решение владельца): не переводить строки UI.
- Не менять `ENCRYPTION_KEY_SALT` и `SECRET_KEY` на инстансе с подключёнными аккаунтами; `.env` не коммитить и не вставлять в чат.
