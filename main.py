# -*- coding: utf-8 -*-
# !/usr/bin/python
import os

from huawei import HuaWei


def main():
    huawei = HuaWei("config.ini")
    huawei.start_process()
    huawei.stop_process()


if __name__ == '__main__':
    banner = """
        ooooo   ooooo                           .oooooo..o                     oooo    oooo  o8o  oooo  oooo  
        `888'   `888'                          d8P'    `Y8                     `888   .8P'   `"'  `888  `888  
         888     888  oooo oooo    ooo         Y88bo.       .ooooo.   .ooooo.   888  d8'    oooo   888   888  
         888ooooo888   `88. `88.  .8'           `"Y8888o.  d88' `88b d88' `"Y8  88888[      `888   888   888  
         888     888    `88..]88..8'   8888888      `"Y88b 888ooo888 888        888`88b.     888   888   888  
         888     888     `888'`888'            oo     .d8P 888    .o 888   .o8  888  `88b.   888   888   888  
        o888o   o888o     `8'  `8'             8""88888P'  `Y8bod8P' `Y8bod8P' o888o  o888o o888o o888o o888o                                                                                                                                                                             
    """
    print(banner)
    main()
