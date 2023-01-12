import gettext

i18n = gettext.translation('main', localedir='locales', languages=['en'])
_ = i18n.gettext
