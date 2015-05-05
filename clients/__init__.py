import configparser


def get_settings(section=None):
    """
    Returns settings
    :param section:
    :return:
    """
    config = configparser.ConfigParser()
    config.read('settings.txt')
    if section:
        return config[section]
    else:
        return config
