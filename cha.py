import os
import sqlite3
import read
import argparse
import configparser


def upgrade():
    reader = read.reader()
    reader.load_files()
    del reader


def cal_len(txt):
    len_txt = len(str(txt))
    len_utf8 = len(str(txt).encode('utf-8'))
    size = int((len_utf8 - len_txt) / 2 + len_txt)
    return size


get_record = """SELECT level,music_id,score_max FROM chusan_user_music_detail"""

create = """CREATE TABLE user_music_detail (
    music_id integer,
    music_level integer,
    score_max integer,
    primary key(music_level,music_id)
);
"""

create_result = """CREATE TABLE result (
    music_id integer,
    music_name varchar(30) not null,
    music_level integer,
    level_name varchar(10),
    music_rate float,
    score_max integer,
    rating float,
    primary key(music_level,music_id)
);
"""

insert = """INSERT into user_music_detail(music_level,music_id,score_max) values(?,?,?);"""

insert_result = """INSERT into result(  music_id,
                                        music_level,
                                        score_max,
                                        music_name,
                                        level_name,
                                        music_rate,
                                        rating) values(?,?,?,?,?,?,0);"""

get_result = """SELECT *
FROM user_music_detail 
INNER JOIN music_detail 
ON user_music_detail.music_id=music_detail.music_id
AND user_music_detail.music_level=music_detail.music_level
"""

update = """update result set rating=? where (music_id,music_level)=(?,?); """

if __name__ == "__main__":

    conn = sqlite3.connect(".\\music_level.sqlite")
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = cur.fetchall()

    if not table or 'music_detail' not in table[0]:
        reader = read.reader()
        reader.createTable()
        reader.load_files()
        del reader
    cur.close()
    conn.close()
    parser = argparse.ArgumentParser()
    parser.add_argument("--upgrade",
                        "-u",
                        help="to upgrade music level database",
                        action='store_true')
    parser.add_argument("--best",
                        "-b",
                        help="show the number of best record you play",
                        type=int,
                        default=30)
    args = parser.parse_args()
    if args.upgrade:
        upgrade()
        exit(1)

    shownumber = 30
    if args.best:
        shownumber = args.best

    conf = configparser.ConfigParser()
    conf.read(".\\config.cfg")
    dir = os.getcwd()
    sql_dir = conf.get(section='path', option='sql_dir')

    os.chdir(sql_dir)
    connDB = sqlite3.connect('.\\db.sqlite')
    curDB = connDB.cursor()
    record = curDB.execute(get_record)

    os.chdir(dir)
    conn = sqlite3.connect(".\\music_level.sqlite")
    cur = conn.cursor()

    try:
        cur.execute(create)
    except Exception as e:
        if str(e) == "table user_music_detail already exists":
            pass
        else:
            print(e)
    cur.execute("DELETE FROM user_music_detail;")

    cur.executemany(insert, record.fetchall())

    try:
        cur.execute(create_result)
    except Exception as e:
        if str(e) == "table result already exists":
            pass
        else:
            print(e)
    cur.execute("DELETE FROM result;")

    conn.commit()
    curDB.close()
    connDB.close()

    #select datalist:(music_id,
    # music_level,
    # score_max,
    # music_id,
    # music_name,
    # music_level,
    # level_name,
    # music_rate,
    # music_rate_decimal)

    #insert datalist:(music_id,
    # music_level,
    # score_max,
    # music_name,
    # level_name,
    # music_rate,
    # )

    result = cur.execute(get_result)
    for Result in result.fetchall():
        cur.executemany(insert_result,
                        [(Result[0], Result[1], Result[2], Result[4],
                          Result[6], Result[7] + Result[8] / 100.0)])
    conn.commit()

    temp = cur.execute("""SELECT music_id,
                                music_level,
                                score_max,
                                music_rate FROM result""")
    for row in temp.fetchall():
        rate_0 = row[3]
        score = row[2]
        music_id = row[0]
        music_level = row[1]
        if score > 100_9000:
            rate_fin = rate_0 + 2.15
        elif score > 100_7500:
            rate_fin = rate_0 + 2 + 0.1 * (score - 100_7500) / 1000
        elif score > 100_5000:
            rate_fin = rate_0 + 1.5 + 0.1 * (score - 100_5000) / 500
        elif score > 100_0000:
            rate_fin = rate_0 + 1 + 0.1 * (score - 100_0000) / 1000
        elif score > 97_5000:
            rate_fin = rate_0 + 0 + 0.1 * (score - 97_5000) / 2500
        elif score > 92_5000:
            rate_fin = rate_0 - 3 + 0.1 * (score - 92_5000) / 2500
        elif score > 90_0000:
            rate_fin = rate_0 - 5 + 0.1 * (score - 90_0000) / 1250
        else:
            rate_fin = 0
        rate_fin = ('%.4f' % rate_fin)
        cur.executemany(update, [(rate_fin, music_id, music_level)])
    conn.commit()

    #print result
    sel = cur.execute(
        "SELECT music_name,level_name,music_rate,score_max,rating FROM result ORDER BY rating DESC"
    )

        # get print width of result
    widths = [0, 8, 4, 7, 7]
    for i in range(shownumber):
        temp = sel.fetchone()
        if not i:
            for j in range(5):
                widths[j] = cal_len(str(temp[j]))
        else:
            for j in range(5):
                widths[j] = max(cal_len(str(temp[j])), widths[j])

    sel = cur.execute(
        "SELECT music_name,level_name,music_rate,score_max,rating FROM result ORDER BY rating DESC"
    )

        # print head
    head=['No.','song','level','rate','score','rating']
    print('{0:^4}'.format(head[0]), end='\t')
    for i in range(5):
        print('{0:^{width}}'.format((head[i+1]),width=widths[i]),end='\t')
    print()

        # print consulting result
    for i in range(shownumber):
        print('{0:^4}'.format(i + 1), end='\t')
        temp = sel.fetchone()
        for j in range(5):
            print('{0:^{width}}'.format(temp[j],
                                        width=widths[j] -
                                        (cal_len(str(temp[j])) - len(str(temp[j])))),
                  end='\t')
        print()

    cur.close()
    conn.close()
