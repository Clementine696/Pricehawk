#!/usr/bin/env python
# -*- coding: utf-8 -*-

with open('backend/logos/logo_data_uri.txt', 'r') as f:
    data_uri = f.read().strip()

with open('backend/services/email_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_text = '🦅 PriceHawk Alert'
new_text = f'<img src="{data_uri}" alt="PriceHawk Logo" style="width: 50px; height: 50px; vertical-align: middle; margin-right: 10px;" /> PriceHawk Alert'

new_content = content.replace(old_text, new_text)

with open('backend/services/email_service.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('✓ Logo embedded')
