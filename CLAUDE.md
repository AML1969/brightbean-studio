# BrightBean Studio — заметки для Claude Code

Форк github.com/brightbeanxyz/brightbean-studio (upstream как remote `upstream`). Документы владельца:
`docs/ЗАПУСК.md` (как запустить), `docs/АНАЛИЗ.md` (архитектура и риски), `docs/ПЛАН.md` (дорожная карта).

## Команды
- Запуск: `python manage.py runserver` + `python manage.py run_studio_worker` (не `process_tasks`).
- Тесты: требуют PostgreSQL 16. `DJANGO_SETTINGS_MODULE=config.settings.test SECRET_KEY=x DATABASE_URL=postgres://postgres:postgres@localhost:5432/brightbean_test pytest -q` (~2 мин, 2736 тестов).
- Проверки перед коммитом: `ruff check . && ruff format --check . && mypy apps/ config/ providers/ tests/ --ignore-missing-imports && python manage.py makemigrations --check --dry-run`.
- Tailwind: `cd theme/static_src && npm run build` (dist гитигнорен).

## Правила
- Ядро (apps/publisher/engine.py, providers/) менять только с тестами; оно защищает от двойной публикации.
- Новая платформа затрагивает ~15 файлов: providers/<x>.py, providers/__init__.py, PlatformCredential.Platform (+ миграции credentials и social_accounts), SocialAccount.PLATFORM_CHAR_LIMITS/PLATFORM_FIELD_CONFIG, apps/api/limits.py, шаблоны иконок и connect-страницы, тесты в tests/providers/.
- Изменения, полезные upstream (исправления багов, тесты), оформлять отдельными небольшими коммитами, чтобы их можно было предложить в PR.
- Русские тексты в документах, код и коммиты на английском допустимы; не переводить строки интерфейса вразнобой до этапа русификации.
- Не менять ENCRYPTION_KEY_SALT и SECRET_KEY на инстансе с подключёнными аккаунтами.
