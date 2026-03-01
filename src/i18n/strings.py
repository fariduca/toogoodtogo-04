"""Translation string catalog for the Telegram bot.

Key-first dictionary: each key maps to {"en": "...", "ru": "..."}.

Naming convention: {domain}_{action}_{variant}
Prefixes: start_, help_, settings_, browse_, offer_, reserve_, purchase_,
          reg_, approval_, btn_, err_, notif_

Per FR-006a: numeric values use "Label: {value}" format (no plural forms).
Per FR-006b: date/time/currency formatting is NOT translated.
Per FR-007: user-generated content (titles, descriptions, names) is NOT in this catalog.
"""

STRINGS: dict[str, dict[str, str]] = {
    'err_register_first': {
        'en': '❌ Please use /start to register first.',
        'ru': '❌ Пожалуйста, используйте /start для регистрации.',
    },
    'err_user_not_found': {
        'en': '❌ User not found.',
        'ru': '❌ Пользователь не найден.',
    },
    'err_offer_unavailable': {
        'en': '❌ This offer is no longer available.',
        'ru': '❌ Это предложение больше не доступно.',
    },
    'err_business_not_found': {
        'en': '❌ Business not found.',
        'ru': '❌ Бизнес не найден.',
    },
    'err_invalid_request': {
        'en': '❌ Invalid request',
        'ru': '❌ Неверный запрос',
    },
    'err_business_info_not_found': {
        'en': '❌ Business information not found.',
        'ru': '❌ Информация о бизнесе не найдена.',
    },
    'err_reservation_not_found': {
        'en': '❌ Reservation not found.',
        'ru': '❌ Бронирование не найдено.',
    },
    'err_offer_not_found': {
        'en': '❌ Offer not found.',
        'ru': '❌ Предложение не найдено.',
    },
    'err_associated_offer_not_found': {
        'en': '❌ Associated offer not found.',
        'ru': '❌ Связанное предложение не найдено.',
    },
    'err_unauthorized': {
        'en': '❌ Unauthorized action.',
        'ru': '❌ Несанкционированное действие.',
    },
    'settings_header': {
        'en': (
            '⚙️ **Settings**\n'
            '\n'
            '**Language:** {language}\n'
            '**Notifications:** {notification_status}\n'
            ''
        ),
        'ru': (
            '⚙️ **Настройки**\n'
            '\n'
            '**Язык:** {language}\n'
            '**Уведомления:** {notification_status}\n'
            ''
        ),
    },
    'settings_notification_enabled': {
        'en': '✅ Enabled',
        'ru': '✅ Включены',
    },
    'settings_notification_disabled': {
        'en': '❌ Disabled',
        'ru': '❌ Отключены',
    },
    'settings_select_language': {
        'en': '🌐 Select your language:',
        'ru': '🌐 Выберите язык:',
    },
    'settings_language_changed': {
        'en': '✅ Language changed to {language_name}!',
        'ru': '✅ Язык изменён на {language_name}!',
    },
    'settings_invalid_language': {
        'en': '❌ Invalid language selection.',
        'ru': '❌ Неверный выбор языка.',
    },
    'btn_toggle_notifications': {
        'en': '🔔 Toggle Notifications',
        'ru': '🔔 Уведомления',
    },
    'btn_change_language': {
        'en': '🌐 Change Language',
        'ru': '🌐 Сменить язык',
    },
    'btn_language_en': {
        'en': 'English 🇬🇧',
        'ru': 'English 🇬🇧',
    },
    'btn_language_ru': {
        'en': 'Русский 🇷🇺',
        'ru': 'Русский 🇷🇺',
    },
    'btn_view_offer': {
        'en': 'View Offer',
        'ru': 'Посмотреть',
    },
    'btn_browse_all': {
        'en': '🌍 All Offers',
        'ru': '🌍 Все предложения',
    },
    'btn_browse_nearby': {
        'en': '📍 Nearby (5km)',
        'ru': '📍 Рядом (5 км)',
    },
    'btn_browse_ending': {
        'en': '⏰ Ending Soon',
        'ru': '⏰ Скоро заканчивается',
    },
    'btn_browse_prev': {
        'en': '⬅️ Previous',
        'ru': '⬅️ Назад',
    },
    'btn_browse_next': {
        'en': '➡️ Next',
        'ru': '➡️ Далее',
    },
    'btn_browse_view': {
        'en': 'View: {title}...',
        'ru': 'Смотреть: {title}...',
    },
    'btn_back_browse': {
        'en': '« Back to Browse',
        'ru': '« Назад к списку',
    },
    'btn_back_list': {
        'en': '« Back to List',
        'ru': '« Назад к списку',
    },
    'btn_reserve': {
        'en': '🛒 Reserve',
        'ru': '🛒 Забронировать',
    },
    'btn_confirm_reserve': {
        'en': '✅ Confirm Reservation',
        'ru': '✅ Подтвердить бронь',
    },
    'btn_browse_more': {
        'en': '🛍️ Browse More Deals',
        'ru': '🛍️ Ещё предложения',
    },
    'btn_my_reservations': {
        'en': '📋 My Reservations',
        'ru': '📋 Мои бронирования',
    },
    'btn_cancel_reservation': {
        'en': '🗑️ Cancel Reservation',
        'ru': '🗑️ Отменить бронь',
    },
    'btn_yes_cancel': {
        'en': '✅ Yes, cancel',
        'ru': '✅ Да, отменить',
    },
    'btn_keep_reservation': {
        'en': '❌ Keep reservation',
        'ru': '❌ Оставить бронь',
    },
    'btn_confirm_cash': {
        'en': 'Confirm Cash Purchase',
        'ru': 'Подтвердить оплату наличными',
    },
    'btn_cancel': {
        'en': '« Cancel',
        'ru': '« Отмена',
    },
    'btn_back': {
        'en': '« Back',
        'ru': '« Назад',
    },
    'btn_pause_offer': {
        'en': '⏸️ Pause',
        'ru': '⏸️ Пауза',
    },
    'btn_resume_offer': {
        'en': '▶️ Resume',
        'ru': '▶️ Возобновить',
    },
    'btn_edit_offer': {
        'en': '✏️ Edit',
        'ru': '✏️ Редактировать',
    },
    'btn_end_offer': {
        'en': '🛑 End Now',
        'ru': '🛑 Завершить',
    },
    'btn_edit_price': {
        'en': '💰 Edit Price',
        'ru': '💰 Изменить цену',
    },
    'btn_edit_quantity': {
        'en': '📦 Edit Quantity',
        'ru': '📦 Изменить количество',
    },
    'btn_edit_description': {
        'en': '📝 Edit Description',
        'ru': '📝 Изменить описание',
    },
    'btn_edit_pickup': {
        'en': '⏰ Edit Pickup Time',
        'ru': '⏰ Изменить время',
    },
    'btn_confirm_end': {
        'en': '✅ Yes, end now',
        'ru': '✅ Да, завершить',
    },
    'btn_cancel_end': {
        'en': '❌ Cancel',
        'ru': '❌ Отмена',
    },
    'btn_approve': {
        'en': '✅ Approve: {name}...',
        'ru': '✅ Одобрить: {name}...',
    },
    'btn_reject': {
        'en': '❌ Reject: {name}...',
        'ru': '❌ Отклонить: {name}...',
    },
    'start_welcome_new': {
        'en': (
            '👋 Welcome to TooGoodToGo, {name}!\n'
            '\n'
            'This bot helps businesses sell excess produce at discounted prices and helps customers discover great deals nearby.\n'
            '\n'
            'To get started, please select your role:'
        ),
        'ru': (
            '👋 Добро пожаловать в TooGoodToGo, {name}!\n'
            '\n'
            'Этот бот помогает бизнесам продавать излишки продуктов по сниженным ценам, а покупателям — находить выгодные предложения рядом.\n'
            '\n'
            'Для начала выберите свою роль:'
        ),
    },
    'start_welcome_back_business': {
        'en': (
            '👋 Welcome back, {name}!\n'
            '\n'
            "You're registered as a business. Here's what you can do:\n"
            '• /newdeal — Post a new excess-produce deal\n'
            '• /myoffers — View and manage your deals\n'
            '• /myreservations — View your reservations'
        ),
        'ru': (
            '👋 С возвращением, {name}!\n'
            '\n'
            'Вы зарегистрированы как бизнес. Вот что вы можете:\n'
            '• /newdeal — Опубликовать новое предложение\n'
            '• /myoffers — Просмотр и управление предложениями\n'
            '• /myreservations — Просмотр бронирований'
        ),
    },
    'start_welcome_back_customer': {
        'en': (
            '👋 Welcome back, {name}!\n'
            '\n'
            "Here's what you can do:\n"
            '• /browse — Discover nearby deals\n'
            '• /myreservations — View your reservations'
        ),
        'ru': (
            '👋 С возвращением, {name}!\n'
            '\n'
            'Вот что вы можете:\n'
            '• /browse — Найти выгодные предложения рядом\n'
            '• /myreservations — Просмотр бронирований'
        ),
    },
    'start_role_business': {
        'en': "🏪 I'm a Business Owner",
        'ru': '🏪 Я владелец бизнеса',
    },
    'start_role_customer': {
        'en': "🛍️ I'm a Customer",
        'ru': '🛍️ Я покупатель',
    },
    'start_deep_link_loading': {
        'en': (
            '📦 Loading offer details...\n'
            '\n'
            'Use /browse to see all available offers, or tap the button below:'
        ),
        'ru': (
            '📦 Загрузка предложения...\n'
            '\n'
            'Используйте /browse чтобы увидеть все предложения, или нажмите кнопку ниже:'
        ),
    },
    'start_deep_link_view': {
        'en': '👆 Tap to view offer details',
        'ru': '👆 Нажмите для просмотра предложения',
    },
    'start_deep_link_invalid': {
        'en': '❌ Invalid offer link. Use /browse to see available offers.',
        'ru': '❌ Недействительная ссылка. Используйте /browse для просмотра предложений.',
    },
    'start_business_invite': {
        'en': (
            '🏪 Business invitation feature coming soon!\n'
            '\n'
            'Use /start to register manually.'
        ),
        'ru': (
            '🏪 Функция приглашения бизнеса скоро появится!\n'
            '\n'
            'Используйте /start для ручной регистрации.'
        ),
    },
    'start_default_message': {
        'en': "I didn't understand that. Try /offers or /newoffer to begin — or send /start for help.",
        'ru': 'Я не понял. Попробуйте /offers или /newoffer — или отправьте /start для помощи.',
    },
    'start_btn_set_language': {
        'en': '🌐 Русский',
        'ru': '🌐 Русский',
    },
    'help_unregistered': {
        'en': (
            '🆘 <b>Help &amp; Commands</b>\n'
            '\n'
            'Welcome to TooGoodToGo Bot! This bot connects businesses with excess produce to customers looking for great deals.\n'
            '\n'
            '<b>Getting Started:</b>\n'
            '• /start — Register as a business or customer\n'
            '\n'
            '<b>For more information, use /start to begin!</b>'
        ),
        'ru': (
            '🆘 <b>Помощь и команды</b>\n'
            '\n'
            'Добро пожаловать в TooGoodToGo Bot! Этот бот связывает бизнесы с излишками продуктов с покупателями, ищущими выгодные предложения.\n'
            '\n'
            '<b>Начало работы:</b>\n'
            '• /start — Зарегистрироваться как бизнес или покупатель\n'
            '\n'
            '<b>Для получения дополнительной информации используйте /start!</b>'
        ),
    },
    'help_business': {
        'en': (
            '🆘 <b>Help for Businesses</b>\n'
            '\n'
            '<b>Post &amp; Manage Deals:</b>\n'
            '• /newdeal — Create a new offer for excess produce\n'
            '• /myoffers — View and manage your offers (pause, resume, edit, end)\n'
            '\n'
            '<b>How it Works:</b>\n'
            '1. Create an offer with details (title, description, price, quantity, pickup time)\n'
            '2. Customers browse and reserve items\n'
            '3. Customers pay on-site when picking up\n'
            '4. You can pause, edit, or end offers anytime\n'
            '\n'
            '<b>Tips:</b>\n'
            '• Set pickup times that work for your business hours\n'
            '• Add clear descriptions and photos for better visibility\n'
            '• Offers expire automatically at the pickup end time\n'
            '\n'
            '<b>Other Commands:</b>\n'
            '• /settings — Manage your preferences\n'
            '• /help — Show this help message\n'
            '\n'
            'Need support? Contact @toogoodtogo_support'
        ),
        'ru': (
            '🆘 <b>Помощь для бизнеса</b>\n'
            '\n'
            '<b>Публикация и управление:</b>\n'
            '• /newdeal — Создать новое предложение\n'
            '• /myoffers — Просмотр и управление предложениями (пауза, возобновление, редактирование, завершение)\n'
            '\n'
            '<b>Как это работает:</b>\n'
            '1. Создайте предложение с деталями (название, описание, цена, количество, время самовывоза)\n'
            '2. Покупатели просматривают и бронируют товары\n'
            '3. Покупатели оплачивают на месте при получении\n'
            '4. Вы можете приостановить, изменить или завершить предложение в любое время\n'
            '\n'
            '<b>Советы:</b>\n'
            '• Устанавливайте удобное время самовывоза\n'
            '• Добавляйте чёткие описания и фото для лучшей видимости\n'
            '• Предложения автоматически истекают по окончании времени самовывоза\n'
            '\n'
            '<b>Другие команды:</b>\n'
            '• /settings — Управление настройками\n'
            '• /help — Показать эту справку\n'
            '\n'
            'Нужна помощь? Напишите @toogoodtogo_support'
        ),
    },
    'help_customer': {
        'en': (
            '🆘 <b>Help for Customers</b>\n'
            '\n'
            '<b>Discover &amp; Reserve:</b>\n'
            '• /browse — Discover available deals nearby\n'
            '• /myreservations — View your active reservations\n'
            '\n'
            '<b>How it Works:</b>\n'
            '1. Browse offers using /browse\n'
            '2. Select an offer to see details\n'
            '3. Reserve your items (payment is on-site)\n'
            '4. Pick up during the specified time window\n'
            '5. Pay in cash/card at the business location\n'
            '\n'
            '<b>Important:</b>\n'
            '• Reservations can be cancelled before pickup time ends\n'
            '• Each reservation has a unique Order ID for pickup\n'
            '• Bring your Order ID when picking up\n'
            '\n'
            '<b>Other Commands:</b>\n'
            '• /settings — Manage your preferences\n'
            '• /help — Show this help message\n'
            '\n'
            'Need support? Contact @toogoodtogo_support'
        ),
        'ru': (
            '🆘 <b>Помощь для покупателей</b>\n'
            '\n'
            '<b>Поиск и бронирование:</b>\n'
            '• /browse — Найти предложения рядом\n'
            '• /myreservations — Просмотр активных бронирований\n'
            '\n'
            '<b>Как это работает:</b>\n'
            '1. Просматривайте предложения через /browse\n'
            '2. Выберите предложение для подробностей\n'
            '3. Забронируйте товар (оплата на месте)\n'
            '4. Заберите в указанное время\n'
            '5. Оплатите наличными или картой на месте\n'
            '\n'
            '<b>Важно:</b>\n'
            '• Бронирования можно отменить до окончания времени самовывоза\n'
            '• Каждое бронирование имеет уникальный номер заказа\n'
            '• Покажите номер заказа при получении\n'
            '\n'
            '<b>Другие команды:</b>\n'
            '• /settings — Управление настройками\n'
            '• /help — Показать эту справку\n'
            '\n'
            'Нужна помощь? Напишите @toogoodtogo_support'
        ),
    },
    'browse_header': {
        'en': (
            '🔍 Browse Deals\n'
            '\n'
            "Choose how you'd like to discover deals:"
        ),
        'ru': (
            '🔍 Обзор предложений\n'
            '\n'
            'Выберите способ поиска:'
        ),
    },
    'browse_no_deals': {
        'en': (
            '😔 No deals available right now.\n'
            'Check back soon for new offers!'
        ),
        'ru': (
            '😔 Сейчас нет доступных предложений.\n'
            'Загляните позже!'
        ),
    },
    'browse_location_required': {
        'en': (
            '📍 Location-based filtering requires you to share your location.\n'
            'Use /browse to try other filters.'
        ),
        'ru': (
            '📍 Для фильтрации по расстоянию нужно отправить геолокацию.\n'
            'Используйте /browse для других фильтров.'
        ),
    },
    'browse_no_deals_filter': {
        'en': (
            '😔 No deals {filter_name} right now.\n'
            'Try a different filter or check back later!'
        ),
        'ru': (
            '😔 Нет предложений {filter_name} прямо сейчас.\n'
            'Попробуйте другой фильтр или загляните позже!'
        ),
    },
    'browse_filter_all': {
        'en': 'matching your criteria',
        'ru': 'по вашим критериям',
    },
    'browse_filter_nearby': {
        'en': 'nearby',
        'ru': 'поблизости',
    },
    'browse_filter_ending': {
        'en': 'ending soon',
        'ru': 'скоро заканчивающихся',
    },
    'browse_page_header': {
        'en': (
            '🛍️ **Available Deals** (Page {current}/{total})\n'
            '\n'
            ''
        ),
        'ru': (
            '🛍️ **Доступные предложения** (Страница {current}/{total})\n'
            '\n'
            ''
        ),
    },
    'browse_ends_in': {
        'en': ' ⚡ Ends in {hours}h',
        'ru': ' ⚡ Осталось {hours}ч',
    },
    'browse_offer_detail_header': {
        'en': (
            '🏪 **{business_name}**\n'
            '\n'
            '📦 **{title}**\n'
            '{description}\n'
            '\n'
            '💰 **Price:** ${price} per unit\n'
            '📊 **Available:** {remaining}/{total} units\n'
            '📍 **Location:** {address}, {city} {postal}\n'
            '📞 **Contact:** {phone}\n'
            '🕐 **Pickup Window:**\n'
            '   {pickup_start} -\n'
            '   {pickup_end}\n'
            '\n'
            '💳 **Payment:** On-site (cash or card)\n'
            ''
        ),
        'ru': (
            '🏪 **{business_name}**\n'
            '\n'
            '📦 **{title}**\n'
            '{description}\n'
            '\n'
            '💰 **Цена:** ${price} за единицу\n'
            '📊 **В наличии:** {remaining}/{total} шт.\n'
            '📍 **Адрес:** {address}, {city} {postal}\n'
            '📞 **Контакт:** {phone}\n'
            '🕐 **Время самовывоза:**\n'
            '   {pickup_start} -\n'
            '   {pickup_end}\n'
            '\n'
            '💳 **Оплата:** На месте (наличными или картой)\n'
            ''
        ),
    },
    'offers_empty': {
        'en': (
            '🔍 No active offers available right now.\n'
            '\n'
            'Check back later or use /register to post your own deals!'
        ),
        'ru': (
            '🔍 Сейчас нет активных предложений.\n'
            '\n'
            'Загляните позже или используйте /register для публикации своих предложений!'
        ),
    },
    'offers_header': {
        'en': (
            '🛍️ **Available Offers**\n'
            ''
        ),
        'ru': (
            '🛍️ **Доступные предложения**\n'
            ''
        ),
    },
    'offers_item_count': {
        'en': (
            '   📦 {remaining} items available\n'
            ''
        ),
        'ru': (
            '   📦 {remaining} шт. в наличии\n'
            ''
        ),
    },
    'offers_tap_details': {
        'en': (
            '\n'
            '\n'
            'Tap an offer to see details and purchase.'
        ),
        'ru': (
            '\n'
            '\n'
            'Нажмите на предложение для подробностей и покупки.'
        ),
    },
    'offers_listing_failed': {
        'en': '❌ Failed to load offers. Please try again later.',
        'ru': '❌ Не удалось загрузить предложения. Попробуйте позже.',
    },
    'offers_invalid_selection': {
        'en': '❌ Invalid offer selection.',
        'ru': '❌ Неверный выбор предложения.',
    },
    'offers_detail_paused': {
        'en': (
            '⏸️ **PAUSED** - Not currently available\n'
            '\n'
            ''
        ),
        'ru': (
            '⏸️ **ПРИОСТАНОВЛЕНО** — Временно недоступно\n'
            '\n'
            ''
        ),
    },
    'offers_detail_sold_out': {
        'en': (
            '🔴 **SOLD OUT**\n'
            '\n'
            ''
        ),
        'ru': (
            '🔴 **РАСПРОДАНО**\n'
            '\n'
            ''
        ),
    },
    'offers_detail_expired': {
        'en': (
            '⏰ **EXPIRED**\n'
            '\n'
            ''
        ),
        'ru': (
            '⏰ **ИСТЕКЛО**\n'
            '\n'
            ''
        ),
    },
    'offers_detail_ended': {
        'en': (
            '🛑 **ENDED**\n'
            '\n'
            ''
        ),
        'ru': (
            '🛑 **ЗАВЕРШЕНО**\n'
            '\n'
            ''
        ),
    },
    'offers_detail_failed': {
        'en': '❌ Failed to load offer details.',
        'ru': '❌ Не удалось загрузить детали предложения.',
    },
    'offers_back_to_list': {
        'en': 'Use /offers or /browse to see available offers.',
        'ru': 'Используйте /offers или /browse для просмотра предложений.',
    },
    'reserve_invalid_request': {
        'en': '❌ Invalid reservation request',
        'ru': '❌ Неверный запрос на бронирование',
    },
    'reserve_customers_only': {
        'en': '❌ Only customers can make reservations.',
        'ru': '❌ Только покупатели могут бронировать.',
    },
    'reserve_quantity_exceeded': {
        'en': (
            '❌ Only {remaining} units available.\n'
            'Please try again with a lower quantity.'
        ),
        'ru': (
            '❌ В наличии только {remaining} шт.\n'
            'Попробуйте меньшее количество.'
        ),
    },
    'reserve_confirm_prompt': {
        'en': (
            '📋 **Confirm Reservation**\n'
            '\n'
            '**Deal:** {title}\n'
            '**Business:** {business_name}\n'
            '**Quantity:** {quantity}\n'
            '**Total:** ${total}\n'
            '\n'
            '**Pickup at:**\n'
            '{address}\n'
            '{city}, {postal}\n'
            '\n'
            '**Pickup Window:**\n'
            '{pickup_start} - {pickup_end}\n'
            '\n'
            '💳 **Payment on-site** (cash or card)\n'
            '\n'
            'Ready to reserve?'
        ),
        'ru': (
            '📋 **Подтверждение бронирования**\n'
            '\n'
            '**Предложение:** {title}\n'
            '**Бизнес:** {business_name}\n'
            '**Количество:** {quantity}\n'
            '**Итого:** ${total}\n'
            '\n'
            '**Адрес самовывоза:**\n'
            '{address}\n'
            '{city}, {postal}\n'
            '\n'
            '**Время самовывоза:**\n'
            '{pickup_start} - {pickup_end}\n'
            '\n'
            '💳 **Оплата на месте** (наличными или картой)\n'
            '\n'
            'Готовы забронировать?'
        ),
    },
    'reserve_invalid_confirmation': {
        'en': '❌ Invalid confirmation request',
        'ru': '❌ Неверный запрос подтверждения',
    },
    'reserve_failed': {
        'en': '❌ Reservation failed. Offer no longer available.',
        'ru': '❌ Бронирование не удалось. Предложение больше недоступно.',
    },
    'reserve_decrement_failed': {
        'en': '❌ Failed to reserve. Please try again.',
        'ru': '❌ Не удалось забронировать. Попробуйте ещё раз.',
    },
    'reserve_locked_out': {
        'en': (
            '❌ {message}\n'
            '\n'
            'The deal may have just sold out or is locked by another customer. Please try again or browse other offers.'
        ),
        'ru': (
            '❌ {message}\n'
            '\n'
            'Возможно, товар только что был распродан или заблокирован другим покупателем. Попробуйте ещё раз или просмотрите другие предложения.'
        ),
    },
    'reserve_confirmed': {
        'en': (
            '🎉 **Reservation Confirmed!**\n'
            '\n'
            '**Order ID:** `{order_id}`\n'
            '**Deal:** {title}\n'
            '**Quantity:** {quantity}\n'
            '**Amount to Pay:** ${total}\n'
            '\n'
            '📍 **Pickup Location:**\n'
            '{business_name}\n'
            '{address}\n'
            '{city}, {postal}\n'
            '📞 {phone}\n'
            '\n'
            '🕐 **Pickup Window:**\n'
            '{pickup_start} - {pickup_end}\n'
            '\n'
            '💳 **Payment:** Pay on-site (cash or card)\n'
            '\n'
            '📱 Show this Order ID when picking up your order.\n'
            'Use /myreservations to view all your reservations.'
        ),
        'ru': (
            '🎉 **Бронирование подтверждено!**\n'
            '\n'
            '**Номер заказа:** `{order_id}`\n'
            '**Предложение:** {title}\n'
            '**Количество:** {quantity}\n'
            '**К оплате:** ${total}\n'
            '\n'
            '📍 **Адрес самовывоза:**\n'
            '{business_name}\n'
            '{address}\n'
            '{city}, {postal}\n'
            '📞 {phone}\n'
            '\n'
            '🕐 **Время самовывоза:**\n'
            '{pickup_start} - {pickup_end}\n'
            '\n'
            '💳 **Оплата:** На месте (наличными или картой)\n'
            '\n'
            '📱 Покажите номер заказа при получении.\n'
            'Используйте /myreservations для просмотра бронирований.'
        ),
    },
    'reserve_my_empty': {
        'en': (
            "📭 You don't have any active reservations.\n"
            '\n'
            'Use /browse to discover deals!'
        ),
        'ru': (
            '📭 У вас нет активных бронирований.\n'
            '\n'
            'Используйте /browse для поиска предложений!'
        ),
    },
    'reserve_my_header': {
        'en': (
            '📋 **Your Reservations**\n'
            '\n'
            ''
        ),
        'ru': (
            '📋 **Ваши бронирования**\n'
            '\n'
            ''
        ),
    },
    'reserve_already_status': {
        'en': '❌ This reservation has already been {status}.',
        'ru': '❌ Это бронирование уже {status}.',
    },
    'reserve_cancel_expired': {
        'en': (
            '❌ Cannot cancel reservation after the pickup window has ended.\n'
            '\n'
            'Pickup window ended at {end_time}.'
        ),
        'ru': (
            '❌ Нельзя отменить бронирование после окончания времени самовывоза.\n'
            '\n'
            'Время самовывоза истекло: {end_time}.'
        ),
    },
    'reserve_cancel_expired_short': {
        'en': '❌ Cannot cancel reservation after the pickup window has ended.',
        'ru': '❌ Нельзя отменить бронирование после окончания времени самовывоза.',
    },
    'reserve_cancel_prompt': {
        'en': (
            '🗑️ **Cancel Reservation?**\n'
            '\n'
            '**Order ID:** `{order_id}`\n'
            '**Deal:** {title}\n'
            '**Quantity:** {quantity} units\n'
            '**Total:** €{total}\n'
            '\n'
            '⚠️ Cancelling will return the items to inventory for others to reserve.\n'
            '\n'
            'Are you sure you want to cancel?'
        ),
        'ru': (
            '🗑️ **Отменить бронирование?**\n'
            '\n'
            '**Номер заказа:** `{order_id}`\n'
            '**Предложение:** {title}\n'
            '**Количество:** {quantity} шт.\n'
            '**Итого:** €{total}\n'
            '\n'
            '⚠️ При отмене товары вернутся в наличие для других покупателей.\n'
            '\n'
            'Вы уверены, что хотите отменить?'
        ),
    },
    'reserve_cancelled_success': {
        'en': (
            '✅ **Reservation Cancelled**\n'
            '\n'
            'Order ID `{order_id}` has been cancelled.\n'
            '{quantity} units have been returned to inventory.\n'
            '\n'
            'Use /browse to find other deals!'
        ),
        'ru': (
            '✅ **Бронирование отменено**\n'
            '\n'
            'Заказ `{order_id}` отменён.\n'
            '{quantity} шт. возвращены в наличие.\n'
            '\n'
            'Используйте /browse для поиска других предложений!'
        ),
    },
    'reserve_cancel_failed': {
        'en': '❌ Failed to cancel reservation. Please try again or contact support.',
        'ru': '❌ Не удалось отменить бронирование. Попробуйте позже или обратитесь в поддержку.',
    },
    'reserve_kept': {
        'en': '✅ Reservation kept. Use /myreservations to view your reservations.',
        'ru': '✅ Бронирование сохранено. Используйте /myreservations для просмотра.',
    },
    'purchase_invalid_action': {
        'en': '❌ Invalid purchase action.',
        'ru': '❌ Неверное действие покупки.',
    },
    'purchase_items_header': {
        'en': (
            '🛒 **Purchase Items**\n'
            '\n'
            'Offer ID: {offer_id}\n'
            '\n'
            'Select items to purchase:\n'
            '\n'
            'Database query implementation pending.\n'
            '\n'
            'For MVP: Cash payment at venue.'
        ),
        'ru': (
            '🛒 **Покупка**\n'
            '\n'
            'ID предложения: {offer_id}\n'
            '\n'
            'Выберите товары:\n'
            '\n'
            'Реализация запроса к БД в процессе.\n'
            '\n'
            'Для MVP: Оплата наличными на месте.'
        ),
    },
    'purchase_initiate_failed': {
        'en': '❌ Failed to initiate purchase.',
        'ru': '❌ Не удалось начать покупку.',
    },
    'purchase_invalid_confirmation': {
        'en': '❌ Invalid confirmation.',
        'ru': '❌ Неверное подтверждение.',
    },
    'purchase_confirmed': {
        'en': (
            '✅ **Purchase Confirmed!**\n'
            '\n'
            'Offer ID: {offer_id}\n'
            'Payment: Cash at venue\n'
            '\n'
            '📍 Pickup Instructions:\n'
            'Visit the venue during the offer time window.\n'
            'Show this confirmation to the business.\n'
            '\n'
            'Your reservation is held. Please arrive on time!\n'
            '\n'
            'Use /cancel <purchase_id> if you need to cancel.'
        ),
        'ru': (
            '✅ **Покупка подтверждена!**\n'
            '\n'
            'ID предложения: {offer_id}\n'
            'Оплата: Наличными на месте\n'
            '\n'
            '📍 Инструкции по получению:\n'
            'Посетите место в указанное время.\n'
            'Покажите это подтверждение бизнесу.\n'
            '\n'
            'Ваше бронирование сохранено. Пожалуйста, приходите вовремя!\n'
            '\n'
            'Используйте /cancel <purchase_id> для отмены.'
        ),
    },
    'purchase_confirm_failed': {
        'en': '❌ Purchase confirmation failed. Please try again.',
        'ru': '❌ Подтверждение покупки не удалось. Попробуйте ещё раз.',
    },
    'purchase_cancel_usage': {
        'en': (
            'Usage: /cancel <purchase_id>\n'
            'Example: /cancel 123e4567-e89b-12d3-a456-426614174000'
        ),
        'ru': (
            'Использование: /cancel <purchase_id>\n'
            'Пример: /cancel 123e4567-e89b-12d3-a456-426614174000'
        ),
    },
    'purchase_cancelled': {
        'en': (
            '✅ Purchase {purchase_id} has been canceled.\n'
            '\n'
            'The items have been returned to inventory.\n'
            'No refund needed (cash payment at venue).'
        ),
        'ru': (
            '✅ Покупка {purchase_id} отменена.\n'
            '\n'
            'Товары возвращены в наличие.\n'
            'Возврат не требуется (оплата наличными на месте).'
        ),
    },
    'purchase_cancel_failed': {
        'en': '❌ Failed to cancel purchase {purchase_id}. Please try again.',
        'ru': '❌ Не удалось отменить покупку {purchase_id}. Попробуйте ещё раз.',
    },
    'offer_need_register': {
        'en': '❌ You need to register first. Use /start to begin.',
        'ru': '❌ Сначала нужно зарегистрироваться. Используйте /start.',
    },
    'offer_business_only': {
        'en': "❌ Only business accounts can post deals. If you're a business, please register with /start",
        'ru': '❌ Только бизнес-аккаунты могут публиковать предложения. Если вы бизнес, зарегистрируйтесь через /start',
    },
    'offer_no_business': {
        'en': "❌ You don't have a registered business yet. Use /start to register.",
        'ru': '❌ У вас ещё нет зарегистрированного бизнеса. Используйте /start для регистрации.',
    },
    'offer_pending_verification': {
        'en': "❌ Your business is still pending verification. You'll be notified when you can start posting deals.",
        'ru': '❌ Ваш бизнес ещё на проверке. Мы уведомим вас, когда вы сможете публиковать предложения.',
    },
    'offer_start_creation': {
        'en': (
            "🎉 Let's create a new deal for {business_name}!\n"
            '\n'
            "First, what's the title of your deal?\n"
            'Example: Fresh Bakery Box, Mixed Produce Bag, etc.\n'
            '\n'
            'Type /cancel anytime to stop.'
        ),
        'ru': (
            '🎉 Создаём новое предложение для {business_name}!\n'
            '\n'
            'Для начала, как называется ваше предложение?\n'
            'Пример: Свежая выпечка, Набор овощей и т.д.\n'
            '\n'
            'Введите /cancel для отмены.'
        ),
    },
    'offer_title_validation': {
        'en': '❌ Title must be between 3 and 100 characters. Please try again:',
        'ru': '❌ Название должно быть от 3 до 100 символов. Попробуйте ещё раз:',
    },
    'offer_ask_description': {
        'en': (
            'Great! Now provide a description (10-200 characters):\n'
            'Example: Mixed seasonal produce, perfect for soups and salads'
        ),
        'ru': (
            'Отлично! Теперь введите описание (10-200 символов):\n'
            'Пример: Сезонные овощи, идеально для супов и салатов'
        ),
    },
    'offer_desc_validation': {
        'en': '❌ Description must be between 10 and 200 characters. Please try again:',
        'ru': '❌ Описание должно быть от 10 до 200 символов. Попробуйте ещё раз:',
    },
    'offer_ask_category': {
        'en': (
            'What category best describes this deal?\n'
            'Options: MEALS, BAKERY, PRODUCE, OTHER\n'
            '\n'
            'Reply with one of these options:'
        ),
        'ru': (
            'Какая категория лучше всего описывает предложение?\n'
            'Варианты: MEALS, BAKERY, PRODUCE, OTHER\n'
            '\n'
            'Ответьте одним из вариантов:'
        ),
    },
    'offer_category_invalid': {
        'en': '❌ Invalid category. Please choose: MEALS, BAKERY, PRODUCE, or OTHER',
        'ru': '❌ Неверная категория. Выберите: MEALS, BAKERY, PRODUCE или OTHER',
    },
    'offer_ask_price': {
        'en': (
            "What's the price per unit? (e.g., 5.99)\n"
            'This is the discounted price customers will pay:'
        ),
        'ru': (
            'Какова цена за единицу? (например, 5.99)\n'
            'Это скидочная цена для покупателей:'
        ),
    },
    'offer_price_invalid': {
        'en': '❌ Invalid price. Please enter a positive number (e.g., 5.99):',
        'ru': '❌ Неверная цена. Введите положительное число (например, 5.99):',
    },
    'offer_ask_quantity': {
        'en': (
            'How many units are available?\n'
            'Enter a whole number (e.g., 10):'
        ),
        'ru': (
            'Сколько единиц доступно?\n'
            'Введите целое число (например, 10):'
        ),
    },
    'offer_quantity_invalid': {
        'en': '❌ Invalid quantity. Please enter a positive whole number:',
        'ru': '❌ Неверное количество. Введите положительное целое число:',
    },
    'offer_ask_pickup_start': {
        'en': (
            'When can customers start picking up?\n'
            'Enter the start time in format: YYYY-MM-DD HH:MM\n'
            'Example: 2025-11-30 14:00'
        ),
        'ru': (
            'Когда покупатели могут начать забирать?\n'
            'Введите время начала в формате: ГГГГ-ММ-ДД ЧЧ:ММ\n'
            'Пример: 2025-11-30 14:00'
        ),
    },
    'offer_pickup_start_past': {
        'en': '❌ Pickup start time must be in the future. Please try again:',
        'ru': '❌ Время начала должно быть в будущем. Попробуйте ещё раз:',
    },
    'offer_pickup_format_invalid': {
        'en': (
            '❌ Invalid format. Use: YYYY-MM-DD HH:MM\n'
            'Example: 2025-11-30 14:00'
        ),
        'ru': (
            '❌ Неверный формат. Используйте: ГГГГ-ММ-ДД ЧЧ:ММ\n'
            'Пример: 2025-11-30 14:00'
        ),
    },
    'offer_ask_pickup_end': {
        'en': (
            'When should pickup end?\n'
            'Enter the end time in format: YYYY-MM-DD HH:MM\n'
            'Example: 2025-11-30 18:00'
        ),
        'ru': (
            'Когда заканчивается время самовывоза?\n'
            'Введите время окончания в формате: ГГГГ-ММ-ДД ЧЧ:ММ\n'
            'Пример: 2025-11-30 18:00'
        ),
    },
    'offer_pickup_end_before_start': {
        'en': '❌ Pickup end time must be after start time. Please try again:',
        'ru': '❌ Время окончания должно быть после начала. Попробуйте ещё раз:',
    },
    'offer_pickup_window_exceeded': {
        'en': '❌ Pickup window cannot exceed 24 hours. Please enter a shorter end time:',
        'ru': '❌ Окно самовывоза не может превышать 24 часа. Введите более раннее время окончания:',
    },
    'offer_pickup_end_format_invalid': {
        'en': (
            '❌ Invalid format. Use: YYYY-MM-DD HH:MM\n'
            'Example: 2025-11-30 18:00'
        ),
        'ru': (
            '❌ Неверный формат. Используйте: ГГГГ-ММ-ДД ЧЧ:ММ\n'
            'Пример: 2025-11-30 18:00'
        ),
    },
    'offer_ask_photo': {
        'en': (
            'Would you like to add a photo of your deal?\n'
            'Send a photo now, or type SKIP to continue without a photo.'
        ),
        'ru': (
            'Хотите добавить фото предложения?\n'
            'Отправьте фото или введите SKIP чтобы продолжить без фото.'
        ),
    },
    'offer_photo_prompt': {
        'en': 'Please send a photo, or type SKIP to continue without one.',
        'ru': 'Пожалуйста, отправьте фото или введите SKIP чтобы продолжить без фото.',
    },
    'offer_photo_received': {
        'en': '✅ Photo received!',
        'ru': '✅ Фото получено!',
    },
    'offer_summary': {
        'en': (
            '📋 Deal Summary:\n'
            '\n'
            '**Title:** {title}\n'
            '**Description:** {description}\n'
            '**Category:** {category}\n'
            '**Price:** ${price} per unit\n'
            '**Quantity:** {quantity} units\n'
            '**Pickup Window:** {pickup_start} - {pickup_end}\n'
            '**Photo:** {has_photo}\n'
            '\n'
            'Reply YES to publish this deal, or NO to cancel.'
        ),
        'ru': (
            '📋 Итоги предложения:\n'
            '\n'
            '**Название:** {title}\n'
            '**Описание:** {description}\n'
            '**Категория:** {category}\n'
            '**Цена:** ${price} за единицу\n'
            '**Количество:** {quantity} шт.\n'
            '**Время самовывоза:** {pickup_start} - {pickup_end}\n'
            '**Фото:** {has_photo}\n'
            '\n'
            'Ответьте YES для публикации или NO для отмены.'
        ),
    },
    'offer_photo_yes': {
        'en': 'Yes ✅',
        'ru': 'Да ✅',
    },
    'offer_photo_no': {
        'en': 'No',
        'ru': 'Нет',
    },
    'offer_creation_cancelled': {
        'en': '❌ Deal creation cancelled. Use /newdeal to start over.',
        'ru': '❌ Создание предложения отменено. Используйте /newdeal чтобы начать заново.',
    },
    'offer_published': {
        'en': (
            '🎉 Deal published successfully!\n'
            '\n'
            '**{title}**\n'
            'Customers can now discover and reserve your deal.\n'
            '\n'
            'Share this link to promote your deal:\n'
            '{share_link}\n'
            '\n'
            'Commands:\n'
            '• /mydeals — Manage your deals\n'
            '• /newdeal — Create another deal'
        ),
        'ru': (
            '🎉 Предложение опубликовано!\n'
            '\n'
            '**{title}**\n'
            'Покупатели теперь могут найти и забронировать ваше предложение.\n'
            '\n'
            'Поделитесь ссылкой:\n'
            '{share_link}\n'
            '\n'
            'Команды:\n'
            '• /mydeals — Управление предложениями\n'
            '• /newdeal — Создать ещё одно'
        ),
    },
    'offer_cancel_newdeal': {
        'en': 'Deal creation cancelled.',
        'ru': 'Создание предложения отменено.',
    },
    'reg_welcome': {
        'en': (
            'Welcome to business registration! 🏪\n'
            '\n'
            "Let's get your business set up to post offers.\n"
            '\n'
            'First, what is your business name?'
        ),
        'ru': (
            'Добро пожаловать в регистрацию бизнеса! 🏪\n'
            '\n'
            'Давайте настроим ваш бизнес для публикации предложений.\n'
            '\n'
            'Для начала, как называется ваш бизнес?'
        ),
    },
    'reg_name_validation': {
        'en': 'Business name must be between 3 and 100 characters. Please try again:',
        'ru': 'Название бизнеса должно быть от 3 до 100 символов. Попробуйте ещё раз:',
    },
    'reg_name_received': {
        'en': (
            'Great! Business name: {name}\n'
            '\n'
            'Now, please provide your venue address.\n'
            'Format: Street Address, City\n'
            'Example: 123 Main St, Springfield'
        ),
        'ru': (
            'Отлично! Название бизнеса: {name}\n'
            '\n'
            'Теперь укажите адрес.\n'
            'Формат: Улица, Город\n'
            'Пример: ул. Главная 123, Москва'
        ),
    },
    'reg_address_validation': {
        'en': 'Please provide a valid address (minimum 5 characters):',
        'ru': 'Введите корректный адрес (не менее 5 символов):',
    },
    'reg_ask_coordinates': {
        'en': (
            'Perfect! Now I need the coordinates of your venue.\n'
            '\n'
            "Please send your location using Telegram's location sharing feature, or provide coordinates in the format: latitude, longitude\n"
            'Example: 37.7749, -122.4194'
        ),
        'ru': (
            'Отлично! Теперь мне нужны координаты.\n'
            '\n'
            'Отправьте геолокацию через Telegram или введите координаты: широта, долгота\n'
            'Пример: 37.7749, -122.4194'
        ),
    },
    'reg_coordinates_invalid': {
        'en': (
            'Invalid coordinates format. Please use: latitude, longitude\n'
            "Or share your location using Telegram's location feature."
        ),
        'ru': (
            'Неверный формат координат. Используйте: широта, долгота\n'
            'Или отправьте геолокацию через Telegram.'
        ),
    },
    'reg_coordinates_range': {
        'en': (
            'Coordinates out of valid range.\n'
            'Latitude: -90 to 90, Longitude: -180 to 180'
        ),
        'ru': (
            'Координаты вне допустимого диапазона.\n'
            'Широта: от -90 до 90, Долгота: от -180 до 180'
        ),
    },
    'reg_coordinates_confirmed': {
        'en': (
            'Location confirmed: {lat}, {lon}\n'
            '\n'
            'Finally, please upload a photo of your business.\n'
            'This helps customers recognize your venue.'
        ),
        'ru': (
            'Локация подтверждена: {lat}, {lon}\n'
            '\n'
            'Наконец, загрузите фото вашего бизнеса.\n'
            'Это поможет покупателям узнать ваше место.'
        ),
    },
    'reg_photo_prompt': {
        'en': 'Please send a photo of your business (not a file or other media).',
        'ru': 'Пожалуйста, отправьте фото вашего бизнеса (не файл или другой медиа-контент).',
    },
    'reg_complete': {
        'en': (
            '✅ Registration complete!\n'
            '\n'
            'Business: {name}\n'
            'Address: {address}\n'
            '\n'
            'Your application is now pending admin verification.\n'
            "You'll be notified once approved. Thank you!"
        ),
        'ru': (
            '✅ Регистрация завершена!\n'
            '\n'
            'Бизнес: {name}\n'
            'Адрес: {address}\n'
            '\n'
            'Ваша заявка ожидает проверки администратором.\n'
            'Мы уведомим вас после одобрения. Спасибо!'
        ),
    },
    'reg_failed': {
        'en': '❌ Registration failed. Please try again later or contact support.',
        'ru': '❌ Регистрация не удалась. Попробуйте позже или обратитесь в поддержку.',
    },
    'reg_cancelled': {
        'en': 'Registration cancelled. Use /register to start again.',
        'ru': 'Регистрация отменена. Используйте /register чтобы начать заново.',
    },
    'reg_select_role': {
        'en': 'Please select a valid role using the keyboard buttons.',
        'ru': 'Пожалуйста, выберите роль с помощью кнопок клавиатуры.',
    },
    'reg_business_setup': {
        'en': (
            "Great! Let's set up your business profile.\n"
            '\n'
            'Please enter your business name:'
        ),
        'ru': (
            'Отлично! Давайте настроим ваш бизнес-профиль.\n'
            '\n'
            'Введите название бизнеса:'
        ),
    },
    'reg_customer_complete': {
        'en': (
            "✅ You're all set!\n"
            '\n'
            'You can now:\n'
            '• /browse — Discover nearby deals\n'
            '• /myreservations — View your reservations\n'
            '\n'
            'Happy shopping! 🛍️'
        ),
        'ru': (
            '✅ Всё готово!\n'
            '\n'
            'Теперь вы можете:\n'
            '• /browse — Найти предложения рядом\n'
            '• /myreservations — Просмотр бронирований\n'
            '\n'
            'Удачных покупок! 🛍️'
        ),
    },
    'reg_name_short': {
        'en': 'Business name is too short. Please enter a valid business name:',
        'ru': 'Название слишком короткое. Введите корректное название бизнеса:',
    },
    'reg_name_confirm': {
        'en': (
            'Business: {name}\n'
            '\n'
            'Now, please enter your street address:'
        ),
        'ru': (
            'Бизнес: {name}\n'
            '\n'
            'Теперь введите адрес:'
        ),
    },
    'reg_address_short': {
        'en': 'Address seems too short. Please enter a complete street address:',
        'ru': 'Адрес слишком короткий. Введите полный адрес:',
    },
    'reg_ask_city': {
        'en': 'Please enter your city:',
        'ru': 'Введите город:',
    },
    'reg_city_short': {
        'en': 'City name is too short. Please enter a valid city:',
        'ru': 'Название города слишком короткое. Введите корректный город:',
    },
    'reg_ask_postal': {
        'en': 'Please enter your postal code:',
        'ru': 'Введите почтовый индекс:',
    },
    'reg_postal_short': {
        'en': 'Postal code is too short. Please enter a valid postal code:',
        'ru': 'Почтовый индекс слишком короткий. Введите корректный индекс:',
    },
    'reg_ask_phone': {
        'en': 'Finally, please enter your phone number for customer contact:',
        'ru': 'Наконец, введите номер телефона для связи:',
    },
    'reg_phone_short': {
        'en': 'Phone number seems too short. Please enter a valid phone number:',
        'ru': 'Номер телефона слишком короткий. Введите корректный номер:',
    },
    'reg_error': {
        'en': '❌ Registration error. Please start again with /start',
        'ru': '❌ Ошибка регистрации. Начните заново с /start',
    },
    'reg_business_submitted': {
        'en': (
            '✅ Business registration submitted!\n'
            '\n'
            'Business: {business_name}\n'
            'Address: {address}, {city} {postal}\n'
            'Phone: {phone}\n'
            '\n'
            "Your business is pending admin approval. You'll receive a notification once your business is verified and you can start posting deals.\n"
            '\n'
            'This usually takes 1-2 business days. Thank you for your patience! 🙏'
        ),
        'ru': (
            '✅ Регистрация бизнеса отправлена!\n'
            '\n'
            'Бизнес: {business_name}\n'
            'Адрес: {address}, {city} {postal}\n'
            'Телефон: {phone}\n'
            '\n'
            'Ваш бизнес ожидает одобрения администратором. Вы получите уведомление после проверки и сможете начать публиковать предложения.\n'
            '\n'
            'Обычно это занимает 1-2 рабочих дня. Спасибо за терпение! 🙏'
        ),
    },
    'reg_lifecycle_cancelled': {
        'en': 'Registration cancelled. You can start again anytime with /start',
        'ru': 'Регистрация отменена. Вы можете начать заново в любое время с /start',
    },
    'approval_no_permission_view': {
        'en': "❌ You don't have permission to view pending businesses.",
        'ru': '❌ У вас нет прав для просмотра ожидающих бизнесов.',
    },
    'approval_pending_list': {
        'en': (
            '📋 Pending Businesses:\n'
            '\n'
            'Use /verify <business_id> to approve\n'
            'Use /reject <business_id> <reason> to reject\n'
            '\n'
            'Database query implementation pending.'
        ),
        'ru': (
            '📋 Ожидающие бизнесы:\n'
            '\n'
            'Используйте /verify <business_id> для одобрения\n'
            'Используйте /reject <business_id> <причина> для отклонения\n'
            '\n'
            'Реализация запроса к БД в процессе.'
        ),
    },
    'approval_failed_list': {
        'en': '❌ Failed to retrieve pending businesses.',
        'ru': '❌ Не удалось получить список ожидающих бизнесов.',
    },
    'approval_no_permission': {
        'en': "❌ You don't have permission to approve businesses.",
        'ru': '❌ У вас нет прав для одобрения бизнесов.',
    },
    'approval_verify_usage': {
        'en': (
            'Usage: /verify <business_id>\n'
            'Example: /verify 123e4567-e89b-12d3-a456-426614174000'
        ),
        'ru': (
            'Использование: /verify <business_id>\n'
            'Пример: /verify 123e4567-e89b-12d3-a456-426614174000'
        ),
    },
    'approval_approved': {
        'en': (
            '✅ Business {business_id} has been approved!\n'
            '\n'
            'The business owner will be notified and can now create offers.'
        ),
        'ru': (
            '✅ Бизнес {business_id} одобрен!\n'
            '\n'
            'Владелец будет уведомлён и сможет создавать предложения.'
        ),
    },
    'approval_failed': {
        'en': '❌ Failed to approve business {business_id}. Please check the business ID and try again.',
        'ru': '❌ Не удалось одобрить бизнес {business_id}. Проверьте ID бизнеса и попробуйте ещё раз.',
    },
    'approval_no_permission_reject': {
        'en': "❌ You don't have permission to reject businesses.",
        'ru': '❌ У вас нет прав для отклонения бизнесов.',
    },
    'approval_reject_usage': {
        'en': (
            'Usage: /reject <business_id> <reason>\n'
            'Example: /reject 123e4567-e89b-12d3-a456-426614174000 Incomplete information'
        ),
        'ru': (
            'Использование: /reject <business_id> <причина>\n'
            'Пример: /reject 123e4567-e89b-12d3-a456-426614174000 Неполная информация'
        ),
    },
    'approval_rejected': {
        'en': (
            '❌ Business {business_id} has been rejected.\n'
            '\n'
            'Reason: {reason}\n'
            '\n'
            'The business owner will be notified.'
        ),
        'ru': (
            '❌ Бизнес {business_id} отклонён.\n'
            '\n'
            'Причина: {reason}\n'
            '\n'
            'Владелец будет уведомлён.'
        ),
    },
    'approval_reject_failed': {
        'en': '❌ Failed to reject business {business_id}.',
        'ru': '❌ Не удалось отклонить бизнес {business_id}.',
    },
    'approval_admin_only': {
        'en': '❌ This command is only available to admins.',
        'ru': '❌ Эта команда доступна только администраторам.',
    },
    'approval_none_pending': {
        'en': 'No pending business registrations.',
        'ru': 'Нет ожидающих регистраций бизнесов.',
    },
    'approval_pending_header': {
        'en': (
            '📋 Pending Business Registrations:\n'
            '\n'
            ''
        ),
        'ru': (
            '📋 Ожидающие регистрации бизнесов:\n'
            '\n'
            ''
        ),
    },
    'approval_business_approved': {
        'en': (
            "✅ Business '{business_name}' has been approved!\n"
            'Owner has been notified.'
        ),
        'ru': (
            "✅ Бизнес '{business_name}' одобрен!\n"
            'Владелец уведомлён.'
        ),
    },
    'approval_business_rejected': {
        'en': (
            "❌ Business '{business_name}' has been rejected.\n"
            'Owner has been notified.'
        ),
        'ru': (
            "❌ Бизнес '{business_name}' отклонён.\n"
            'Владелец уведомлён.'
        ),
    },
    'notif_business_approved': {
        'en': (
            "🎉 Great news! Your business '{business_name}' has been approved!\n"
            '\n'
            'You can now start posting deals:\n'
            '• /newdeal — Create your first deal\n'
            '• /myoffers — Manage your offers\n'
            '\n'
            'Welcome to TooGoodToGo! 🚀'
        ),
        'ru': (
            "🎉 Отличные новости! Ваш бизнес '{business_name}' одобрен!\n"
            '\n'
            'Теперь вы можете публиковать предложения:\n'
            '• /newdeal — Создать первое предложение\n'
            '• /myoffers — Управление предложениями\n'
            '\n'
            'Добро пожаловать в TooGoodToGo! 🚀'
        ),
    },
    'notif_business_rejected': {
        'en': (
            'Thank you for your interest in TooGoodToGo.\n'
            '\n'
            "Unfortunately, your business registration for '{business_name}' could not be approved at this time.\n"
            '\n'
            'If you believe this is an error, please contact support.'
        ),
        'ru': (
            'Благодарим за интерес к TooGoodToGo.\n'
            '\n'
            "К сожалению, регистрация бизнеса '{business_name}' не может быть одобрена в данный момент.\n"
            '\n'
            'Если вы считаете это ошибкой, обратитесь в поддержку.'
        ),
    },
    'offer_mgmt_business_only': {
        'en': '❌ Only business accounts can manage offers.',
        'ru': '❌ Только бизнес-аккаунты могут управлять предложениями.',
    },
    'offer_mgmt_no_business': {
        'en': "❌ You don't have a registered business yet.",
        'ru': '❌ У вас ещё нет зарегистрированного бизнеса.',
    },
    'offer_mgmt_empty': {
        'en': (
            "📦 You haven't posted any offers yet for {business_name}.\n"
            '\n'
            'Use /newdeal to create your first offer!'
        ),
        'ru': (
            '📦 У вас ещё нет предложений для {business_name}.\n'
            '\n'
            'Используйте /newdeal для создания первого предложения!'
        ),
    },
    'offer_mgmt_header': {
        'en': (
            '📦 **Your Offers** ({count} total)\n'
            ''
        ),
        'ru': (
            '📦 **Ваши предложения** ({count} всего)\n'
            ''
        ),
    },
    'offer_mgmt_time_until': {
        'en': 'Until {time}',
        'ru': 'До {time}',
    },
    'offer_mgmt_expired': {
        'en': 'Expired',
        'ru': 'Истекло',
    },
    'offer_edit_header': {
        'en': (
            '✏️ **Edit {title}**\n'
            '\n'
            'Current settings:\n'
            '• Price: €{price}\n'
            '• Quantity: {remaining}/{total}\n'
            '• Description: {description}...\n'
            '• Pickup ends: {pickup_end}\n'
            '\n'
            'What would you like to edit?'
        ),
        'ru': (
            '✏️ **Редактирование {title}**\n'
            '\n'
            'Текущие настройки:\n'
            '• Цена: €{price}\n'
            '• Количество: {remaining}/{total}\n'
            '• Описание: {description}...\n'
            '• Самовывоз до: {pickup_end}\n'
            '\n'
            'Что вы хотите изменить?'
        ),
    },
    'offer_edit_cannot': {
        'en': '❌ Cannot edit offer in {state} state.',
        'ru': '❌ Нельзя редактировать предложение в состоянии {state}.',
    },
    'offer_edit_session_expired': {
        'en': '❌ Session expired. Use /myoffers to try again.',
        'ru': '❌ Сессия истекла. Используйте /myoffers чтобы попробовать снова.',
    },
    'offer_edit_price_prompt': {
        'en': (
            '💰 **Edit Price**\n'
            '\n'
            'Current price: €{price}\n'
            '\n'
            'Enter new price (e.g., 5.50):\n'
            'Type /cancel to abort.'
        ),
        'ru': (
            '💰 **Изменение цены**\n'
            '\n'
            'Текущая цена: €{price}\n'
            '\n'
            'Введите новую цену (например, 5.50):\n'
            'Введите /cancel для отмены.'
        ),
    },
    'offer_edit_quantity_prompt': {
        'en': (
            '📦 **Edit Quantity**\n'
            '\n'
            'Current remaining: {remaining}\n'
            '\n'
            'Enter new quantity available:\n'
            'Type /cancel to abort.'
        ),
        'ru': (
            '📦 **Изменение количества**\n'
            '\n'
            'Текущий остаток: {remaining}\n'
            '\n'
            'Введите новое количество:\n'
            'Введите /cancel для отмены.'
        ),
    },
    'offer_edit_desc_prompt': {
        'en': (
            '📝 **Edit Description**\n'
            '\n'
            'Current: {description}\n'
            '\n'
            'Enter new description (10-200 characters):\n'
            'Type /cancel to abort.'
        ),
        'ru': (
            '📝 **Изменение описания**\n'
            '\n'
            'Текущее: {description}\n'
            '\n'
            'Введите новое описание (10-200 символов):\n'
            'Введите /cancel для отмены.'
        ),
    },
    'offer_edit_pickup_prompt': {
        'en': (
            '⏰ **Edit Pickup End Time**\n'
            '\n'
            'Current: {pickup_end}\n'
            '\n'
            'Enter new end time (format: HH:MM, e.g., 18:30):\n'
            'Type /cancel to abort.'
        ),
        'ru': (
            '⏰ **Изменение времени окончания самовывоза**\n'
            '\n'
            'Текущее: {pickup_end}\n'
            '\n'
            'Введите новое время (формат: ЧЧ:ММ, например, 18:30):\n'
            'Введите /cancel для отмены.'
        ),
    },
    'offer_edit_price_invalid': {
        'en': '❌ Price must be greater than 0. Try again:',
        'ru': '❌ Цена должна быть больше 0. Попробуйте ещё раз:',
    },
    'offer_edit_price_updated': {
        'en': (
            '✅ Price updated to €{price}\n'
            '\n'
            'Use /myoffers to see your offers.'
        ),
        'ru': (
            '✅ Цена обновлена: €{price}\n'
            '\n'
            'Используйте /myoffers для просмотра предложений.'
        ),
    },
    'offer_edit_price_format': {
        'en': '❌ Invalid price format. Enter a number (e.g., 5.50):',
        'ru': '❌ Неверный формат цены. Введите число (например, 5.50):',
    },
    'offer_edit_quantity_invalid': {
        'en': '❌ Quantity cannot be negative. Try again:',
        'ru': '❌ Количество не может быть отрицательным. Попробуйте ещё раз:',
    },
    'offer_edit_quantity_updated': {
        'en': (
            '✅ Quantity updated to {quantity} units\n'
            '\n'
            'Use /myoffers to see your offers.'
        ),
        'ru': (
            '✅ Количество обновлено: {quantity} шт.\n'
            '\n'
            'Используйте /myoffers для просмотра предложений.'
        ),
    },
    'offer_end_cannot': {
        'en': '❌ Cannot end offer in {state} state.',
        'ru': '❌ Нельзя завершить предложение в состоянии {state}.',
    },
    'offer_end_prompt': {
        'en': (
            '🛑 **End {title}?**\n'
            '\n'
            'This will permanently end the offer and remove it from customer view.\n'
            'Currently {remaining} units remaining.\n'
            '\n'
            'This action cannot be undone.'
        ),
        'ru': (
            '🛑 **Завершить {title}?**\n'
            '\n'
            'Это навсегда завершит предложение и уберёт его из видимости покупателей.\n'
            'Осталось {remaining} шт.\n'
            '\n'
            'Это действие нельзя отменить.'
        ),
    },
    'offer_ended': {
        'en': (
            '🛑 **{title}** has been ended.\n'
            '\n'
            'The offer is no longer visible to customers.'
        ),
        'ru': (
            '🛑 **{title}** завершено.\n'
            '\n'
            'Предложение больше не видно покупателям.'
        ),
    },
    'offer_end_cancelled': {
        'en': '✅ Offer ending cancelled. Use /myoffers to manage your offers.',
        'ru': '✅ Завершение отменено. Используйте /myoffers для управления предложениями.',
    },
    'offer_pause_cannot': {
        'en': '❌ Cannot pause offer in {state} state.',
        'ru': '❌ Нельзя приостановить предложение в состоянии {state}.',
    },
    'offer_paused': {
        'en': (
            '⏸️ **{title}** is now paused.\n'
            '\n'
            "Customers won't see this offer in browse results. Use /myoffers to resume it."
        ),
        'ru': (
            '⏸️ **{title}** приостановлено.\n'
            '\n'
            'Покупатели не увидят это предложение в результатах поиска. Используйте /myoffers для возобновления.'
        ),
    },
    'offer_resume_cannot': {
        'en': '❌ Cannot resume offer in {state} state.',
        'ru': '❌ Нельзя возобновить предложение в состоянии {state}.',
    },
    'offer_resume_expired': {
        'en': '❌ Cannot resume expired offer. Pickup window ended at {end_time}.',
        'ru': '❌ Нельзя возобновить истёкшее предложение. Время самовывоза закончилось: {end_time}.',
    },
    'offer_resumed': {
        'en': (
            '▶️ **{title}** is now active!\n'
            '\n'
            'Customers can now see and reserve this offer.'
        ),
        'ru': (
            '▶️ **{title}** снова активно!\n'
            '\n'
            'Покупатели теперь могут видеть и бронировать это предложение.'
        ),
    },
    'offer_pause_usage': {
        'en': (
            'Usage: /pause <offer_id>\n'
            'Example: /pause 123e4567-e89b-12d3-a456-426614174000\n'
            '\n'
            'This will temporarily pause your offer, preventing new purchases while keeping it visible to customers.'
        ),
        'ru': (
            'Использование: /pause <offer_id>\n'
            'Пример: /pause 123e4567-e89b-12d3-a456-426614174000\n'
            '\n'
            'Это временно приостановит ваше предложение, запретив новые покупки, но оставив его видимым для покупателей.'
        ),
    },
    'offer_pause_invalid_id': {
        'en': (
            '❌ Invalid offer ID format: {offer_id}\n'
            'Please provide a valid UUID.'
        ),
        'ru': (
            '❌ Неверный формат ID предложения: {offer_id}\n'
            'Укажите корректный UUID.'
        ),
    },
    'offer_pause_no_permission': {
        'en': "❌ You don't have permission to pause this offer.",
        'ru': '❌ У вас нет прав для приостановки этого предложения.',
    },
    'offer_pause_already': {
        'en': "ℹ️ Offer '{title}' is already paused.",
        'ru': "ℹ️ Предложение '{title}' уже приостановлено.",
    },
    'offer_pause_cannot_status': {
        'en': (
            "❌ Cannot pause offer '{title}'.\n"
            'Current status: {status}\n'
            'Only active offers can be paused.'
        ),
        'ru': (
            "❌ Нельзя приостановить предложение '{title}'.\n"
            'Текущий статус: {status}\n'
            'Только активные предложения можно приостановить.'
        ),
    },
    'offer_pause_success': {
        'en': (
            '⏸️ Offer paused successfully!\n'
            '\n'
            '**{title}**\n'
            '\n'
            'Your offer is now paused. Customers can still view it, but they cannot make new purchases.\n'
            '\n'
            'To resume, use: /resume {offer_id}'
        ),
        'ru': (
            '⏸️ Предложение приостановлено!\n'
            '\n'
            '**{title}**\n'
            '\n'
            'Ваше предложение приостановлено. Покупатели могут его видеть, но не могут совершать покупки.\n'
            '\n'
            'Для возобновления: /resume {offer_id}'
        ),
    },
    'offer_pause_failed': {
        'en': (
            '❌ Failed to pause offer.\n'
            'Error: {error}\n'
            '\n'
            'Please try again later.'
        ),
        'ru': (
            '❌ Не удалось приостановить предложение.\n'
            'Ошибка: {error}\n'
            '\n'
            'Попробуйте позже.'
        ),
    },
    'offer_resume_usage': {
        'en': (
            'Usage: /resume <offer_id>\n'
            'Example: /resume 123e4567-e89b-12d3-a456-426614174000\n'
            '\n'
            'This will resume your paused offer, allowing customers to purchase again.'
        ),
        'ru': (
            'Использование: /resume <offer_id>\n'
            'Пример: /resume 123e4567-e89b-12d3-a456-426614174000\n'
            '\n'
            'Это возобновит приостановленное предложение, позволяя покупателям снова покупать.'
        ),
    },
    'offer_resume_invalid_id': {
        'en': (
            '❌ Invalid offer ID format: {offer_id}\n'
            'Please provide a valid UUID.'
        ),
        'ru': (
            '❌ Неверный формат ID предложения: {offer_id}\n'
            'Укажите корректный UUID.'
        ),
    },
    'offer_resume_no_permission': {
        'en': "❌ You don't have permission to resume this offer.",
        'ru': '❌ У вас нет прав для возобновления этого предложения.',
    },
    'offer_resume_already_active': {
        'en': "ℹ️ Offer '{title}' is already active.",
        'ru': "ℹ️ Предложение '{title}' уже активно.",
    },
    'offer_resume_cannot_status': {
        'en': (
            "❌ Cannot resume offer '{title}'.\n"
            'Current status: {status}\n'
            'Only paused offers can be resumed.'
        ),
        'ru': (
            "❌ Нельзя возобновить предложение '{title}'.\n"
            'Текущий статус: {status}\n'
            'Только приостановленные предложения можно возобновить.'
        ),
    },
    'offer_lifecycle_edit_usage': {
        'en': (
            'Usage: /edit <offer_id>\n'
            'Example: /edit 123e4567-e89b-12d3-a456-426614174000'
        ),
        'ru': (
            'Использование: /edit <offer_id>\n'
            'Пример: /edit 123e4567-e89b-12d3-a456-426614174000'
        ),
    },
    'offer_lifecycle_edit_invalid_id': {
        'en': '❌ Invalid offer ID format: {offer_id}',
        'ru': '❌ Неверный формат ID предложения: {offer_id}',
    },
    'offer_lifecycle_edit_not_found': {
        'en': '❌ Offer not found: {offer_id}',
        'ru': '❌ Предложение не найдено: {offer_id}',
    },
    'offer_lifecycle_edit_no_permission': {
        'en': "❌ You don't have permission to edit this offer.",
        'ru': '❌ У вас нет прав для редактирования этого предложения.',
    },
    'offer_lifecycle_edit_cannot': {
        'en': (
            '❌ Cannot edit offer in {status} status.\n'
            'Only active or paused offers can be edited.'
        ),
        'ru': (
            '❌ Нельзя редактировать предложение в статусе {status}.\n'
            'Только активные или приостановленные предложения можно редактировать.'
        ),
    },
    'offer_lifecycle_edit_header': {
        'en': (
            '**Edit Offer: {title}**\n'
            '\n'
            'What would you like to edit?'
        ),
        'ru': (
            '**Редактирование: {title}**\n'
            '\n'
            'Что вы хотите изменить?'
        ),
    },
    'offer_lifecycle_edit_cancelled': {
        'en': '✅ Edit canceled.',
        'ru': '✅ Редактирование отменено.',
    },
    'offer_lifecycle_edit_select_price': {
        'en': 'Select an item to edit price:',
        'ru': 'Выберите товар для изменения цены:',
    },
    'offer_lifecycle_edit_select_qty': {
        'en': 'Select an item to edit quantity:',
        'ru': 'Выберите товар для изменения количества:',
    },
    'offer_lifecycle_edit_failed': {
        'en': (
            '❌ Failed to start editing.\n'
            'Error: {error}'
        ),
        'ru': (
            '❌ Не удалось начать редактирование.\n'
            'Ошибка: {error}'
        ),
    },
    'btn_edit_item_prices': {
        'en': '📝 Edit Item Prices',
        'ru': '📝 Цены товаров',
    },
    'btn_edit_item_quantities': {
        'en': '📦 Edit Item Quantities',
        'ru': '📦 Количество товаров',
    },
    'offer_lifecycle_edit_item_not_found': {
        'en': '❌ Item not found.',
        'ru': '❌ Товар не найден.',
    },
    'offer_lifecycle_edit_price_prompt': {
        'en': (
            '**Edit Price: {item_name}**\n'
            '\n'
            'Current price: ${price}\n'
            '\n'
            'Enter new price (e.g., 5.99):'
        ),
        'ru': (
            '**Изменение цены: {item_name}**\n'
            '\n'
            'Текущая цена: ${price}\n'
            '\n'
            'Введите новую цену (например, 5.99):'
        ),
    },
    'offer_lifecycle_edit_price_negative': {
        'en': '❌ Price cannot be negative. Please try again.',
        'ru': '❌ Цена не может быть отрицательной. Попробуйте ещё раз.',
    },
    'offer_lifecycle_edit_price_updated': {
        'en': (
            '✅ Price updated successfully!\n'
            '\n'
            '**{item_name}**: ${price}'
        ),
        'ru': (
            '✅ Цена обновлена!\n'
            '\n'
            '**{item_name}**: ${price}'
        ),
    },
    'offer_lifecycle_edit_price_invalid': {
        'en': '❌ Invalid price format. Please enter a number (e.g., 5.99).',
        'ru': '❌ Неверный формат цены. Введите число (например, 5.99).',
    },
    'offer_lifecycle_edit_price_failed': {
        'en': (
            '❌ Failed to update price.\n'
            'Error: {error}'
        ),
        'ru': (
            '❌ Не удалось обновить цену.\n'
            'Ошибка: {error}'
        ),
    },
    'offer_lifecycle_edit_qty_prompt': {
        'en': (
            '**Edit Quantity: {item_name}**\n'
            '\n'
            'Current quantity: {quantity}\n'
            '\n'
            'Enter new quantity:'
        ),
        'ru': (
            '**Изменение количества: {item_name}**\n'
            '\n'
            'Текущее количество: {quantity}\n'
            '\n'
            'Введите новое количество:'
        ),
    },
    'offer_lifecycle_edit_qty_negative': {
        'en': '❌ Quantity cannot be negative. Please try again.',
        'ru': '❌ Количество не может быть отрицательным. Попробуйте ещё раз.',
    },
    'offer_lifecycle_edit_qty_updated': {
        'en': (
            '✅ Quantity updated successfully!\n'
            '\n'
            '**{item_name}**: {quantity} available'
        ),
        'ru': (
            '✅ Количество обновлено!\n'
            '\n'
            '**{item_name}**: {quantity} в наличии'
        ),
    },
    'offer_lifecycle_edit_qty_invalid': {
        'en': '❌ Invalid quantity. Please enter a whole number.',
        'ru': '❌ Неверное количество. Введите целое число.',
    },
    'offer_lifecycle_edit_qty_failed': {
        'en': (
            '❌ Failed to update quantity.\n'
            'Error: {error}'
        ),
        'ru': (
            '❌ Не удалось обновить количество.\n'
            'Ошибка: {error}'
        ),
    },
    'offer_resume_expired_msg': {
        'en': (
            "❌ Cannot resume offer '{title}'.\n"
            'This offer has expired and can no longer be resumed.'
        ),
        'ru': (
            "❌ Нельзя возобновить предложение '{title}'.\n"
            'Срок действия предложения истёк.'
        ),
    },
    'offer_resume_success': {
        'en': (
            '▶️ Offer resumed successfully!\n'
            '\n'
            '**{title}**\n'
            '\n'
            'Your offer is now active again. Customers can browse and purchase.'
        ),
        'ru': (
            '▶️ Предложение возобновлено!\n'
            '\n'
            '**{title}**\n'
            '\n'
            'Ваше предложение снова активно. Покупатели могут просматривать и покупать.'
        ),
    },
    'offer_resume_failed': {
        'en': (
            '❌ Failed to resume offer.\n'
            'Error: {error}\n'
            '\n'
            'Please try again later.'
        ),
        'ru': (
            '❌ Не удалось возобновить предложение.\n'
            'Ошибка: {error}\n'
            '\n'
            'Попробуйте позже.'
        ),
    },
}
