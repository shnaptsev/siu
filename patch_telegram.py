"""
Патч для исправления проблемы с python-telegram-bot и Python 3.13
Применяется автоматически при импорте
"""
import sys

if sys.version_info >= (3, 13):
    try:
        # Импортируем модуль updater
        import telegram.ext._updater as updater_module
        
        # Получаем оригинальный класс
        OriginalUpdater = updater_module.Updater
        
        # Получаем оригинальные slots
        if hasattr(OriginalUpdater, '__slots__'):
            original_slots = list(OriginalUpdater.__slots__)
            
            # Если __dict__ уже есть, ничего не делаем
            if '__dict__' not in original_slots:
                # Создаем новый список slots с __dict__
                new_slots = tuple(list(original_slots) + ['__dict__'])
                
                # Создаем новый класс с измененными slots
                namespace = {
                    '__slots__': new_slots,
                    '__module__': OriginalUpdater.__module__,
                }
                
                # Копируем все методы и атрибуты
                for name in dir(OriginalUpdater):
                    if not name.startswith('__') or name in ['__init__', '__new__', '__class__']:
                        attr = getattr(OriginalUpdater, name, None)
                        if attr is not None and not name.startswith('_'):
                            namespace[name] = attr
                
                # Сохраняем оригинальный __init__
                original_init = OriginalUpdater.__init__
                
                # Создаем новый __init__ который устанавливает атрибут
                def new_init(self, *args, **kwargs):
                    # Устанавливаем атрибут через object.__setattr__
                    try:
                        object.__setattr__(self, '_Updater__polling_cleanup_cb', None)
                    except (TypeError, AttributeError):
                        pass
                    # Вызываем оригинальный __init__
                    original_init(self, *args, **kwargs)
                
                namespace['__init__'] = new_init
                
                # Создаем новый класс
                FixedUpdater = type('Updater', (OriginalUpdater,), namespace)
                
                # Заменяем класс в модуле
                updater_module.Updater = FixedUpdater
                # Также заменяем в __all__ если есть
                if hasattr(updater_module, '__all__'):
                    updater_module.__all__ = tuple(
                        'Updater' if x == 'Updater' else x 
                        for x in updater_module.__all__
                    )
    except Exception as e:
        # Если патч не удался, просто игнорируем (бот все равно может работать)
        # Предупреждение подавлено, так как бот работает без патча при правильной версии библиотеки
        pass

