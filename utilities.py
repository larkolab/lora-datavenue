#
# / _____)             _              | |
#( (____  _____ ____ _| |_ _____  ____| |__
# \____ \| ___ |    (_   _) ___ |/ ___)  _ \
# _____) ) ____| | | || |_| ____( (___| | | |
#(______/|_____)_|_|_| \__)_____)\____)_| |_|
#    (C)2016 Semtech
#
#Description: Mimics a map data structure in Python
#
# REMARK: Search for author acknowledgment and check license
#
#License: Revised BSD License, see LICENSE.TXT file include in the project
#
#Maintainer: Miguel Luis
#
class Map(dict):
    def __init__(self, **kwargs):
        super(Map, self).__init__(**kwargs)
        self.__dict__ = self
