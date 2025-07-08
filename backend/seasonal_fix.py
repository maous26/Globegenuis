from datetime import datetime

# Simple check for month values
months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
current_month = datetime.now().month
print(f"Current month: {current_month}")

# Simulate the seasonal periods
seasonal_periods = {
    'summer': {
        'months': [6, 7, 8],  # Juin, Juillet, Août
    },
    'winter': {
        'months': [12, 1, 2],  # Décembre, Janvier, Février
    },
    'spring': {
        'months': [3, 4, 5],  # Mars, Avril, Mai
    },
    'autumn': {
        'months': [9, 10, 11],  # Septembre, Octobre, Novembre
    },
    'yearround_events': {
        'months': 'all',  # Toute l'année
    }
}

# Check which seasons are active
for period, config in seasonal_periods.items():
    is_active = config['months'] == 'all' or current_month in config['months']
    print(f"Period '{period}' active: {is_active}")
