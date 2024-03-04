import xml
import sqlite3
import os
import xml.dom.minidom
import configparser

create = """CREATE TABLE music_detail (
    music_id integer,
    music_name varchar(30) not null,
    music_level integer,
    level_name varchar(10),
    music_rate integer,
    music_rate_decimal integer,
    primary key(music_id,music_level)
);
"""

loadin = """insert into music_detail(music_id, music_name, music_level, level_name, music_rate,
          music_rate_decimal) values(?,?,?,?,?,?);
"""

update = """update music_detail set (music_rate, music_rate_decimal)=(?,?) where (music_id,music_level)=(?,?); """

class reader():
    def __init__(self) -> None:
        conf = configparser.ConfigParser()
        conf.read(".\\config.cfg")
        self.dir = os.getcwd()
        self.bin_dir = conf.get(section='path', option='bin_dir')
        self.opt_dir = conf.get(section='path', option='opt_dir')
        self.conn=sqlite3.connect("music_level.sqlite")
        self.cur=self.conn.cursor()

    def load_xmls(self):
        DOMtree = xml.dom.minidom.parse("Music.xml")
        collection = DOMtree.getElementsByTagName("MusicData")[0]

        name = DOMtree.getElementsByTagName("name")[0]
        music_id = name.getElementsByTagName("id")[0].childNodes[0].data
        music_name = name.getElementsByTagName("str")[0].childNodes[0].data

        fumens = collection.getElementsByTagName("fumens")[0]
        levels = fumens.getElementsByTagName("MusicFumenData")

        for level in levels:
            if level.getElementsByTagName(
                    "enable")[0].childNodes[0].data == "false":
                continue

            Type = level.getElementsByTagName("type")[0]
            music_level = Type.getElementsByTagName("id")[0].childNodes[0].data
            level_name = Type.getElementsByTagName("str")[0].childNodes[0].data

            music_rate = level.getElementsByTagName("level")[0].childNodes[0].data
            music_rate_decimal = level.getElementsByTagName(
                "levelDecimal")[0].childNodes[0].data

            loadin_data_list = [(music_id, music_name, music_level, level_name,
                                music_rate, music_rate_decimal)]
            try:
                self.cur.executemany(loadin, loadin_data_list)
                self.conn.commit()
            except Exception as e:
                if str(
                        e
                ) == "UNIQUE constraint failed: music_detail.music_id, music_detail.music_level":
                    try:
                        self.cur.executemany(update, [
                            (music_rate, music_rate_decimal, music_id, music_level)
                        ])
                        self.conn.commit()
                    except Exception as ex:
                        print(ex)

    def load_files(self):
        #load A000
        os.chdir(self.bin_dir)
        os.chdir('.\\A000\\music')
        files = os.listdir(os.getcwd())
        for file in files:
            if os.path.isfile(file):
                continue
            os.chdir(file)
            self.load_xmls()
            os.chdir("..")

        #load options
        os.chdir(self.dir)
        os.chdir(self.opt_dir)
        opts = os.listdir(os.getcwd())
        for opt in opts:
            os.chdir(self.opt_dir)
            if os.path.isfile(opt):
                continue
            os.chdir(opt)
            try:
                os.chdir('.\\music')
            except Exception as e:
                continue

            files = os.listdir(os.getcwd())
            for file in files:
                if os.path.isfile(file):
                    continue
                os.chdir(file)
                self.load_xmls()
                os.chdir("..")

    def createTable(self):
        try:
            self.cur.execute(create)
        except Exception as e:
            if str(e) == "table song_level already exists":
                pass
            else:
                print(e)

    def __del__(self):
        self.cur.close()
        self.conn.close()

