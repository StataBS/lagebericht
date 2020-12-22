"""
Diese App unterstützt die Prozesse rund um das Erstellen des Covid-19 Lageberichts mails der Medizinischen Dienste
des Kantons Basel-Stadt.

Kontakt: lukas.calmbach@bs.ch
"""

from enum import Enum
import io
import pandas as pd
import streamlit as st
import altair as alt
from altair_saver import save
import locale
from datetime import datetime, timedelta, date
import calendar
import json
import requests
import io
from io import BytesIO
import json
import xlrd
import os
import shutil
from passlib.context import CryptContext
import random

import db
import const
import SessionState 
from queries import qry

STYLE = """
<style>
img {
    max-width: 100%;
}
</style>
"""

__author__ = 'lukas calmbach'
__author_email__ = 'lukas.calmbach@bs.ch'
__version__ = '0.1.16'
version_date = '2020-12-22'

session_state = {}
menu = ''
config = {} # dictionary mit allen Konfigurationseinträgen
df_config = pd.DataFrame()
proxy_dict = {'https': "https://dpdstatasvsql05:dpdstatasvsql05_@proxy1.bs.ch:3128"}
conn = db.get_connection(const.SERVER, const.DATABASE)

def get_config():
    """
    Gibt die Konfiguration in Form eines Dataframes und eines dictionarys zurück.
    Der Dataframe wird verwendet um die Gesamtkonfiguration anzuzeigen und zu editieren.
    Das dictionary wird verwendet, um die records in der App zu verwenden, z.B. 
    als config['schluessel']
    """

    sql = qry['get_konfig']
    cfg_df = db.get_recordset(conn,sql).set_index('schluessel')
    cfg_dic = cfg_df['wert'].to_dict()
    return cfg_df, cfg_dic

def show_summary():  
    """
    Startscreen, zeigt ein paar allgemeine Infos sowie den Log der letzten 2 Tage und den Stand der 
    zu publizierenden Zahlen.
    """
    heute = datetime.strftime(datetime.now(), '%d.%m.%Y')
    st.markdown(f'### Log Einträge')
    sql = qry['log_today']
    df = db.get_recordset(conn,sql).set_index('tag', 'zeit')
    st.write(df)
    st.markdown(f'### Werte ({heute})', unsafe_allow_html=True)
    sql = qry['compare_values']
    df = db.get_recordset(conn,sql).set_index('Feld')
    st.dataframe(df,1000,1000)

def import_file(config):    
    """
    Ruft die stored procedure auf dem db-server auf und startet den Import
    der Einzeldaten
    """

    filename = config['source_path'] + config['source_filename']
    try:
        st.info(f"{config['source_filename']} wird gelesen")
        df = pd.read_excel(filename)   
        
        sql = qry['db_fields']
        df_fields = db.get_recordset(conn, sql)
        raw_fields = df_fields['field_name'].to_list() 
        db_fields = df_fields['db_field_name'].to_list() 

        st.info('Import in DB wird gestartet, dies kann einige Minuten dauern.')
        db.exec_non_query(conn, qry['truncate_rohdaten'])
        db.append_pd_table(df, 'lagebericht_roh', raw_fields)
        st.info(f"{config['source_filename']} wurde in DB importiert: {len(df)} Zeilen")
        # formatiert die list zu einer comma separierten Text im Format [feld 1], [feld 2]...
        raw_fields_str = '[' + '], ['.join(raw_fields) + ']'
        db_fields_str = '[' + '], ['.join(db_fields) + ']'
        sql_cmd = qry['insert_lagebericht'].format(db_fields_str, raw_fields_str)
        if db.exec_non_query(conn, sql_cmd) == 1:
            st.info('Felder wurden in DB Tabelle formatiert')
        else:
            st.warning('Felder konnten in der DB Tabelle nicht formatiert werden')
        archive_file = f"{config['source_path']}archiv\\{date.today().strftime('%Y-%m-%d')}_{config['source_filename']}"
        sql = qry['rowcount_lagebericht_today']
        rows = db.get_value(conn, sql)
        st.info(f"QS: {rows} Zeilen mit Datum heute in Lagebericht-Tabelle")
        shutil.copyfile(filename, archive_file)
        os.remove(filename)
        csv_file = f"imp_{date.today().strftime('%Y-%m-%d')}.csv"
        archive_file = config['source_path'] + 'archiv\\' + csv_file
        
        df.to_csv(archive_file, index=False)
        st.info('Import Datei wurde gelöscht')
    except Exception as ex:
        st.warning(f'Die Datei konnte nicht importiert werden: {ex}')

def calculate_values():
    """
    Aggregiert die Einzelwerte in die Zeitreihetabelle und berechnet die Inzidenzen.
    """

    st.info('Inzidenzen und Differenzen zu Vortags Werten werden berechnet')
    sql = qry['run_update']
    if db.exec_non_query(conn,sql) == 1:
        st.info('Berechnungen wurden durchgeführt, die wichtigsten Resultate sind in untenstehender Tabelle aufgelistet')
    else:
        st.info('Bei den Berechnungen ist ein Problem aufgetreten')
    sql = qry['inzidenzen_qs']
    df = db.get_recordset(conn,sql)
    st.write(df)


def send_test_mail():
    """
    Stellt die Informationen für den Mailversand zusammen und verschickt die Mail an 
    den Testmail Verteiler.
    """

    st.info('Prozess gestartet')
    sql = qry['send_test_mail'].format(session_state.email)
    if db.exec_non_query(conn,sql) == 1:
        st.info('Die Testmail wurde verschickt')
    else:
        st.warning('Beim Versand der Testmail ist ein Problem aufgetreten')

def send_mail():
    if st.checkbox(f"QS durchgeführt ({session_state.user_name})", value=False):
        send_mail_sel = st.checkbox("Mail versenden an Mail Verteiler", value=True)
        send_sms_sel = st.checkbox("SMS versenden an SMS Verteiler", value=True)
        ogd_export_sel = st.checkbox("OGD Export durchführen", value=True)
        
        if st.button("Versand starten"):        
            if ogd_export_sel:
                export_ogd(config)
            if send_mail_sel:
                sql = qry['send_mail']
                st.info('Mail-Versand wurde gestartet')
                if db.exec_non_query(conn,sql) == 1:
                    st.info('Das Lagebericht-Mail wurde verschickt')
                else:
                    st.warning('Beim Versand des Lagebericht-Mails ist ein Problem aufgetreten')
            if send_sms_sel:
                send_sms()
        


def send_sms():
    st.info('sms-Versand wurde gestartet')
    sql = qry['send_sms']
    if db.exec_non_query(conn,sql) == 1:
        st.info('Das Lagebericht-sms wurde an den Verteiler verschickt')
    else:
        st.warning('Beim Versand des Lageberichts-sms ist ein Problem aufgetreten')

def send_test_sms():
    st.info('SMS-Test-Versand wurde gestartet')
    sql = qry['send_test_sms'].format(session_state.email)
    if db.exec_non_query(conn,sql) == 1:
        st.info('Das Test-Lagebericht-SMS wurde an den Verteiler verschickt')
    else:
        st.warning('Beim Versand des Test-Lagebericht-SMS ist ein Problem aufgetreten')


def show_configuration():
    sql = qry['get_html_table'].format('konfig')
    html = db.get_value(conn,sql)
    st.markdown(html, unsafe_allow_html=True)


def get_bl_cases(config):
    url = config['url_covid_faelle_kantone'].format('BL')
    
    s = requests.get(url, proxies=proxy_dict).text
    records = json.loads(s)
    records = records['records']
    df_json = pd.DataFrame(records)
    lst = df_json['fields']
    st.info("Datei mit BL-Fällen wurde geladen")

    for x in lst:
        cmd = qry['update_faelle_bl'].format(x['ncumul_conf'],x['date'])
        if db.exec_non_query(conn,cmd) != 1:
            st.markdown(f'Befehl `{cmd}` konnte nicht ausgeführt werden.')
    st.info("BL Fälle wurden in Datenbank gespeichert")
    sql = qry['show_bl_cases']
    df = db.get_recordset(conn,sql)
    st.dataframe(df, 1000, 1000)


def get_bs_cases(config):
    url = config['url_bs_hospitalisierte']
    
    s = requests.get(url, proxies=proxy_dict).text
    records = json.loads(s)
    records = records['records']
    df_json = pd.DataFrame(records)
    lst = df_json['fields']
    st.info("Datei mit BS-Fällen wurde geladen")

    for x in lst:
        if 'current_hosp_resident' in x:
            # st.write(x['current_hosp_resident'],x['current_hosp'],x['current_icu'],x['date'])
            cmd = qry['update_faelle_bs'].format(x['current_hosp_resident'], 
                x['current_hosp'], 
                x['current_icu'], 
                (1 if x['data_from_all_hosp'] == 'True' else 0),
                x['date'] )
            if db.exec_non_query(conn,cmd) != 1:
                st.markdown(f'Befehl `{cmd}` konnte nicht ausgeführt werden.')
    st.info("BS Hospitalisierte wurden in Datenbank gespeichert")
    sql = qry['show_bs_hospitalised']
    df = db.get_recordset(conn,sql)
    st.dataframe(df, 1000, 1000)
    

def get_ch_cases(config):
    """
    Speichert den BAG lagebericht lokal ab, öffnet die Excel Datei und speichert die CH-Fälle. Da pd.read_excel keinen proxys parameter kennt, muss die 
    Datei zuerst geladen und lokal im Verzeichnis data abgespeichert werden.
    """

    url = config['url_bag_lagebericht']    
    r = requests.get(url,proxies=proxy_dict) # create HTTP response object 
    filename = config['bag_lagebericht_lokal']
    with open(filename,'wb') as f: 
        f.write(r.content) 
    df = pd.read_excel(filename, sheet_name='COVID19 Zahlen',header=6)
    st.info("Excel Datei wurde geladen")
    for i in range(len(df)) : 
        datum = df.loc[i, "Datum"]
        cmd = qry['update_faelle_ch'].format(df.loc[i, "Fallzahlen pro Tag, kumuliert"], datum)
        if db.exec_non_query(conn,cmd) != 1:
            st.markdown(f'Befehl `{cmd}` konnte nicht ausgeführt werden.')
    st.info("CH Fälle wurden in Datenbank gespeichert")
    sql = qry['show_ch_faelle']
    df = db.get_recordset(conn,sql)
    st.dataframe(df, 1000, 1000)
    

def edit_values():
    """
    Erlaubt die Manuell zu erfassenden WErte inzidenz07_loerrach, inzidenz07_haut_rhin und isoliert_aph_bs
    zu erfassen und speichern.
    """

    sql = qry['edit_values_view']
    st.markdown('### Stand Datenbank')
    df = db.get_recordset(conn,sql)
    st.dataframe(df)

    st.markdown('### Werte editieren')
    #datum = st.date_input('Datum (JJJJ-MM-TT')
    datum = st.text_input('Datum (JJJJ-MM-TT')
    sql = qry['get_manual_edit_fields'].format(datum)
    df = db.get_recordset(conn,sql)
    if len(df)>0 : 
        val_loerrach = df.iloc[0]['inzidenz07_loerrach'] 
        val_haut_rhin = df.iloc[0]['inzidenz07_haut_rhin']
        val_aph = df.iloc[0]['isoliert_aph_bs']
    else:
        val_loerrach = None
        val_haut_rhin = None
        val_aph = None
    inzidenz07_loerrach = st.text_input('7-Tage Inzidenz Landeskreis Lörrach', val_loerrach)
    inzidenz07_haut_rhin = st.text_input('7-Tage Inzidenz Département Haut-Rhin', val_haut_rhin)
    isoliert_aph_bs = st.text_input('Isolierte in APHs', val_aph)
    if st.button('Speichern'):
        inzidenz07_loerrach = db.get_db_value(inzidenz07_loerrach,3)
        inzidenz07_haut_rhin = db.get_db_value(inzidenz07_haut_rhin,3)
        isoliert_aph_bs = db.get_db_value(isoliert_aph_bs,2)
        cmd = qry['manual_update'].format(inzidenz07_loerrach, inzidenz07_haut_rhin, isoliert_aph_bs, datum)
        db.exec_non_query(conn,cmd)
        st.info("Datensatz wurde gespeichert.")


def edit_config():
    key = st.selectbox("Wähle Parameter aus",options = df_config.index.to_list())
    value = st.text_input(key, df_config.loc[key]['wert'])
    st.write(df_config.loc[key]['beschreibung'])
    if st.button('Speichern'):
        value = db.get_db_value(value, df_config.loc[key]['typ'])
        cmd = qry['update_config'].format(value, key )
        if db.exec_non_query(conn,cmd) == 1:
            st.info('Der Wert wurde gespeichert')
        else:
            st.warning('Der Wert konnte nicht gespeichert werden')


def make_plots(config):
    """
    Erstellt die 2 Grafiken (attachment des Mailversands): 
    Fig 1. Neue Fälle als Barchart, 7 Tagesmittel als Linie
    Fig2: Fälle Bs kumuliert.
    warum muss ihc hier config übergeben, 
    """

    file = config['export_csv_path'] + config['export_csv_filename_datum']
    try:
        #df = pd.read_csv(file, sep=';')
        sql = qry['plot_data']
        df = db.get_recordset(conn,sql)
        # filtert Nullwerte raus
        # fetch & enable German format & timeFormat locales.
        s = requests.get('https://raw.githubusercontent.com/d3/d3-format/master/locale/de-DE.json', proxies=proxy_dict).text
        de_format = json.loads(s)
        s = requests.get('https://raw.githubusercontent.com/d3/d3-time-format/master/locale/de-DE.json', proxies=proxy_dict).text
        de_time_format = json.loads(s)
        alt.renderers.set_embed_options(formatLocale=de_format, timeFormatLocale=de_time_format)
        
        #locale.setlocale(locale.LC_ALL, "de_CH")
        df['datum'] = df['datum'].apply(lambda x: 
                                            datetime.strptime(x,'%Y-%m-%d'))
        df['7-Tage Schnitt'] = '7-Tage Mittel'
        df['Neumeldungen'] = 'Neumeldungen'
        min_date = '2020-02-29'

        max_date = max(df['datum'].to_list()) 
        day=calendar.monthrange(max_date.year, max_date.month)[1]
        max_date = datetime(max_date.year,max_date.month,day) + timedelta(days=1)
        domain_pd = pd.to_datetime([min_date, max_date]).astype(int) / 10 ** 6
        today = datetime.now().strftime("%d. %b %Y")

        bar = alt.Chart(data=df, title='Neumeldungen BS, Stand: ' + today).encode(    
            ).mark_bar(width = 2).encode(
            x=alt.X('datum:T', axis=alt.Axis(title="",format="%b %y"), scale = alt.Scale(domain=list(domain_pd) )),
            y=alt.Y('faelle_bs:Q', axis=alt.Axis(title="Anzahl Fälle")),
            tooltip=['faelle_bs', 'datum'],
            color=alt.Color('Neumeldungen:N', legend=alt.Legend(title=""))
            )

        line =  bar.mark_line().encode(
            y='mittel_07_tage_bs:Q',
            color=alt.Color('7-Tage Schnitt:N', legend=alt.Legend(title=""))
        )

        fig1 = (bar + line).properties(width=600)

        kumuliert= alt.Chart(data=df, title='Meldungen kumulativ BS, Stand: ' + today).encode(
            ).mark_line(color='blue').encode(
            x=alt.X('datum:T', axis=alt.Axis(title="", format="%b %y"), scale = alt.Scale(domain=list(domain_pd) )),
            y=alt.Y('faelle_bs_kum:Q', axis=alt.Axis(title="Anzahl Fälle")),  # scale = alt.Scale(domain=(0, 4500))
            tooltip=['faelle_bs_kum', 'datum']
            )
                    
        fig2 = kumuliert.properties(width=600)

        st.write(fig1 & fig2)
        save(fig1 & fig2, config['temp_figuren_lokal'])
        st.info(f"Datei wurde gespeichert unter: {config['temp_figuren_lokal']}")
    except Exception as ex:
        st.error(ex)


def get_steps():
    result = {}
    result['import'] = st.checkbox("Import Excel Datei in Datenbank")
    result['extern'] = st.checkbox("Externe Datenquellen importieren", True)
    result['update'] = st.checkbox("Zeitreihe erstellen", True)
    result['plots'] = st.checkbox("Grafiken erzeugen", True)
    result['test_mail']= st.checkbox("Test Mail verschicken", True)
    result['test_sms']= st.checkbox("Test SMS verschicken", True)
    st.markdown('**Anpassungen in der Mail**')

    meldezeit = db.get_value(conn, qry['meldezeit_today'])

    meldezeit = st.text_input("Meldezeit", meldezeit)
    if meldezeit > '':
        cmd = qry['update_meldezeit'].format(meldezeit)
        if db.exec_non_query(conn,cmd) != 1:
            st.warning('meldezeit konnte nicht gespeichert werden')
    use_yesterday = st.checkbox("Für Hospitialisierte-BS-Werte vom Vortag verwenden.", False)
    if use_yesterday:
        cmd = qry['delete_hosp_data_today']
        if db.exec_non_query(conn,cmd) != 1:
            st.warning('das löschen der heutigen Hospitalisierungsdaten hat leider nicht funktioniert')

    comment_text = db.get_value(conn, qry['mail_comment_today'])
    comment_text = st.text_area("Begleittext für den Mailversand", comment_text)
    try:
        cmd = qry['update_mail_comment'].format(comment_text)
        db.exec_non_query(conn,cmd)
    except Exception as ex:
        st.warning('Kommentar konnte nicht gespeichert werden')
    return result

def get_rounded_time_string(t: datetime, interval: int)-> str:
    """
    Gibt einen Zeitstempel zurück, wobei die Minuten auf 15 Minuten gerundet sind
    """
    t = datetime(t.year, t.month, t.day, t.hour, (t.minute - (t.minute % interval)) ) 
    return t.strftime("%H:%M")

def save_reporting_time(start_time):
    reporting_time = get_rounded_time_string(datetime.now(), const.ROUNDED_MINUTES)
    sql = qry['save_reporting_time'].format(reporting_time)
    if db.exec_non_query(conn,sql) == 0:
        print('Meldezeit konnte nicht gespeichert werden')

def show_upload_personen():
    st.set_option('deprecation.showfileUploaderEncoding', False)
    uploaded_file = BytesIO()
    st.markdown("""Hier können Personen geladen werden. Ziehe eine Excel Datei mit allen Personen in untenstehendes Feld.
Bereits in der Datenbank bestehende Personen werden aktualisiert (Identifikation mittels Emailadresse) neue Personen werden angefügt. Bei 
Personen, die auch ein Benutzerkonto haben sollen, muss das Feld Benutzer-Kürzel gefüllt sein.""")
    uploaded_file = st.file_uploader(f"Personen für Verteiler", type=['xlsx'])
        
    if uploaded_file:
        filename = r'.\data\personen.xlsx'
        with open(filename, 'wb') as f: ## Excel File
            f.write(uploaded_file.read()) 
    if st.button("Personenliste abgleichen") and uploaded_file:
        st.info(f"Personen werden eingelesen")
        try:           
            df = pd.read_excel(filename)   
            s = df.to_json()
            # nach json und zurück um alle typen als string zu konvertieren
            # todo: geht ev. noch eleganter, aber ohne das werden Telnr als 7.98374646+10 geladen 
            df = pd.read_json(s)
            st.info('Import in DB wird gestartet.')
            db.append_pd_table(df, 'person_roh', [])
            sql = qry['synch_person_list']
            if db.exec_non_query(conn,sql) == 1:
                st.info(f"Adressen wurden in DB importiert und abgeglichen: {len(df)} Personen")
            else:
                raise Exception("In der Abgleich-Prozedur ist ein Fehler aufgetreten.") 
        except Exception as ex:
            st.warning(f"Beim Einlesen der Personen ist ein Problem aufgetreten: {ex}")


def upload_file(config):
    st.set_option('deprecation.showfileUploaderEncoding', False)
    uploaded_file = BytesIO()
    uploaded_file = st.file_uploader(f"Excel Export Datei ({config['source_filename']})", type=['xlsx'])
    
    auto_import = st.checkbox('Import nach upload starten', True)
        
    if uploaded_file:
        start_time = datetime.now()
        filename = config['source_path'] + config['source_filename']
        with open(filename, 'wb') as f: ## Excel File
            f.write(uploaded_file.read()) 
            save_reporting_time(start_time)
        st.info(f'Die Datei wurde gespeichert unter {filename}, der Import kann gestartet werden.')
        if auto_import:
            steps = {'import': True, 'update': True, 'extern': True, 'plots': True,
                'test_mail': True, 'test_sms': True}
            run_selected_steps(steps, config)
    

def export_ogd(config):
    """
    todo: Aufruf exec [dbo].[sp04_export_csv_lagebericht] funktioniert nicht, vermutlich läuft etwas intern in DeprecationWarningexpoert csv routine falsch, 
    denn die erste Datei wird erzeugt aber leer
    """
    st.info('Prozess OGD Export wurde gestartet')
    try:
        sql = qry['export_ogd_nach_test_datum']
        df = db.get_recordset(conn, sql)
        st.write(df)
        filename = config['export_csv_path'] + 'faelle_nach_test_datum.csv'
        df.to_csv(filename, sep=';', index=False)

        sql = qry['export_ogd_nach_publikations_datum']
        df = db.get_recordset(conn, sql)
        st.write(df)
        filename = config['export_csv_path'] + 'faelle_nach_publikations_datum.csv'
        df.to_csv(filename, sep=';', index=False) 

        sql = qry['export_ogd_detail']
        df = db.get_recordset(conn, sql)
        st.write(df)
        filename = config['export_csv_path'] + config['export_csv_filename_detail']
        df.to_csv(filename, sep=';', index=False) 

        #sql = qry['export_ogd_nach_gemeinden']
        #df = db.get_recordset(conn, sql)
        #st.write(df)
        #filename = config['export_csv_path'] + config['export_csv_filename_gemeinden']
        #df.to_csv(filename, sep=';', index=False) 

        st.info('OGD Dateien wurden erstellt und gespeichert.')
        
    except Exception as ex:
        st.warning(f'Beim Export der OGD Dateien ist ein Problem aufgetreten: {repr(ex)}')

def insert_today_record():
    """
    inserts the today record to the zeitreihe table if missing
    """
    sql = qry['add_today_record']
    return db.exec_non_query(conn, sql)

def run_selected_steps(steps, config):
    """
    führt alle Schritte aus, die im dictonary steps übergeben werden.  
    """
    if steps['import']:
        import_file(config)
    if steps['extern']:
        insert_today_record()
        get_bs_cases(config)
        get_bl_cases(config)
        get_ch_cases(config)
    if steps['update']:
        calculate_values()
    if steps['plots']:
        make_plots(config)
    if steps['test_mail']:
        send_test_mail()
    if steps['test_sms']:
        send_test_sms()
    
    st.info('Alle selektierten Prozesse wurden ausgeführt')
    st.balloons()

def change_password(session_state):
    sql = qry['user_info'].format(session_state.user_name)
    df = db.get_recordset(conn, sql)
    row = df.iloc[0]
    st.markdown(f'Benutzer: {row.nachname} {row.vorname}')
    pwd1 = st.text_input('Neues Passwort',type='password')
    pwd2 = st.text_input('Passwort bestätigen',type='password')
    if st.button('Passwort ändern'):
        if pwd1 == pwd2 and len(pwd1) > 0:
            context = get_crypt_context()
            sql = qry['change_pwd'].format(context.hash(pwd1), row['benutzer'])
            if db.exec_non_query(conn, sql) == 1:
                st.info('Passwort wurde erfolgreich geändert')
            else:
                st.warning('Das Passwort konnte leider nicht geändert werden, kontaktieren sie den Systemadministrator')
        else:
            t.warning('Passwörter stimmen nicht überein, versuchen sie es nochmals')


def delete_person(person_id: int):
    sql = qry['person_delete'].format(person_id)
    if db.exec_non_query(conn, sql) == 1:
        st.info('Der Datensatz wurde erfolgreich gelöscht')
    else:
        st.warning(f'Der Datensatz konnte nicht gelöscht werden.')


def edit_person(person_dic: dict):
    person_id = st.selectbox('Person auswählen:',  options=list(person_dic.keys()),
                   format_func=lambda x: person_dic[x])                   
    sql = qry['person_info'].format(person_id)
    person = db.get_recordset(conn, sql).iloc[0]

    person_str = f"""Nachname:\t{person['nachname']}\n 
Vorname:\t{person['vorname']}\n
Email:\t{person['email']}\n
Mobile:\t{person['mobile']}
"""
    print(person_str)
    st.info(person_str)
    #ist_benutzer = 1 if st.checkbox('Ist Operator/in', value = (person['ist_benutzer'] == 1)) else 0
    
    #col1, col2, col3 = st.beta_columns([0.1, 0.1, 0.5])
    
    #if col1.button('Speichern'):
    #    sql = qry['person_update'].format(nachname, vorname, email, mobile, ist_benutzer, person_id)
    #    if db.exec_non_query(conn, sql) == 1:
    #        st.info('Der Datensatz wurde erfolgreich gespeichert')
    #        st.experimental_rerun()
    #    else:
    ##        st.warning(f'Der Datensatz konnte nicht gespeichert werden.')
    #elif col2.button('Neu'):
    #    sql = qry['person_new']
    #    if db.exec_non_query(conn, sql) == 1:
    #        st.info('Es wurde eine neue Person angelegt')
    #        st.experimental_rerun()
    #    else:
    #        st.warning(f'Die Person konnte nicht angelegt werden.')
    if st.button('Person Löschen'):
        delete_person(person_id)
    
def verteiler_speichern(verteiler_id: int, person_liste:list):
    sql = qry['verteiler_person_empty'].format(verteiler_id)
    if db.exec_non_query(conn, sql) == 1:
        for pers_id in person_liste:
            sql = qry['verteiler_person_insert'].format(pers_id, verteiler_id)
            db.exec_non_query(conn, sql) 
        st.info(f'Der Verteiler wurde gespeichert.')
    else:
        st.warning(f'Der Verteiler wurde gespeichert werden.')

def show_verteiler_verwalten():
    sql = qry['person_all'].format(session_state.user_name)
    df = db.get_recordset(conn, sql)
    
    st.markdown("----")
    st.markdown("**Liste der erfassten Personen**")
    st.write(df)

    sql = qry['person_list'].format(session_state.user_name)
    person_df = db.get_recordset(conn, sql).set_index('id')['name']
    person_dic = person_df.to_dict()
    # Editieren/Inserten von Personen kann man wieder einfügen, wenn das nötig ist.
    edit_person(person_dic)
    show_upload_personen()

    st.markdown('---')
    st.markdown('**Verteiler**')

    sql = sql = qry['lookup_code_list'].format(4)
    verteiler_dic = db.get_recordset(conn, sql).set_index('id')['name'].to_dict()
    verteiler = st.selectbox('Auswahl Verteiler',options=list(verteiler_dic.keys()),
                   format_func=lambda x: verteiler_dic[x])
    
    sql = qry['verteiler_person_bez'].format(verteiler)
    verteiler_pers_list =  db.get_recordset(conn, sql)['person_id'].to_list()
    verteiler_person = st.multiselect(f'Personen zuweisen zu {verteiler_dic[verteiler]} ({len(verteiler_pers_list)})',options=list(person_dic.keys()),
                   format_func=lambda x: person_dic[x], default=verteiler_pers_list)  
    if st.button('Speichern', key='speichern_verteiler'):
        verteiler_speichern(verteiler, verteiler_person)


def plot(df):
    """
    Erstellt eine Zeitreihen-Grafik mit dem dataframe df. df muss eine Spalte Datum enthalten.
    """

    # fetch & enable German format & timeFormat locales.
    s = requests.get('https://raw.githubusercontent.com/d3/d3-format/master/locale/de-DE.json', proxies=proxy_dict).text
    de_format = json.loads(s)
    s = requests.get('https://raw.githubusercontent.com/d3/d3-time-format/master/locale/de-DE.json', proxies=proxy_dict).text
    de_time_format = json.loads(s)
    alt.renderers.set_embed_options(formatLocale=de_format, timeFormatLocale=de_time_format)

    # locale.setlocale(locale.LC_ALL, "de_CH")
    df['datum'] = df['datum'].apply(lambda x: 
        datetime.strptime(x,'%Y-%m-%d'))
    df['7-Tage Schnitt'] = '7-Tage Mittel'
    df['Neumeldungen'] = 'Neumeldungen'

    # calculate the 
    min_date = '2020-02-29'

    max_date = max(df['datum'].to_list()) 
    day=calendar.monthrange(max_date.year, max_date.month)[1]
    max_date = datetime(max_date.year,max_date.month,day) + timedelta(days=1)
    domain_pd = pd.to_datetime([min_date, max_date]).astype(int) / 10 ** 6
    today = datetime.now().strftime("%d. %b %Y")

    line = alt.Chart(data=df, title='Covid Lagebericht App, Stand: ' + today).encode().mark_line().encode(
        x=alt.X('datum:T', axis=alt.Axis(title="",format="%b %y"), scale = alt.Scale(domain=list(domain_pd) )),
        y=alt.Y('value:Q', axis=alt.Axis(title="Anzahl Fälle")),
        tooltip=['datum', 'variable', 'value'],
        color=alt.Color('variable:N', legend=alt.Legend(title=""))
        )

    fig = (line).properties(width=1000).interactive()
    st.write(fig)

def show_werte_ueberpruefen():
    st.markdown(f"### Zeitreihe")
    selected_fields  = st.multiselect('Auswahl Felder', const.FELDER_ZEITREIHE, default = const.FELDER_ZEITREIHE[:3])
    selected_fields_csv = ','.join(selected_fields)
    sql = qry['check_values_table'].format(selected_fields_csv)
    df = db.get_recordset(conn, sql)
    st.dataframe(df)
    df_melted = pd.melt(df,id_vars=['datum'], value_vars=selected_fields)
    plot(df_melted)

    st.markdown(f"### Verstorbene")
    sql = qry['verstorbene']    
    df = db.get_recordset(conn, sql)
    st.dataframe(df)

    st.markdown(f"### Inzidenzen")
    selected_fields  = st.multiselect('Auswahl Inzidenz-Felder', const.FELDER_INZIDENZEN, default = const.FELDER_INZIDENZEN[:7])
    selected_fields_csv = ','.join(selected_fields)
    sql = qry['inzidenzen'].format(selected_fields_csv)
    df = db.get_recordset(conn, sql)
    st.dataframe(df)
    df_melted = pd.melt(df,id_vars=['datum'], value_vars=selected_fields)
    plot(df_melted)

    
def show_menu(session_state):
    menu = st.sidebar.selectbox('Menu:',  options=const.MENU_OPTIONS)
    st.markdown(f'## {menu}')
    with st.beta_expander('', expanded= False):
        st.markdown(const.MENU_DESC[menu],unsafe_allow_html=True)
    selected_steps = {}
    if menu == 'Info':
        show_summary()
    elif menu == 'Datei hochladen':
        upload_file(config)
    elif menu == 'Prozesssteuerung manuell':
        selected_steps = get_steps()
        if st.sidebar.button('Ausführen'): 
            run_selected_steps(selected_steps, config)
    elif menu == 'Konfiguration zeigen':
        show_configuration()
    elif menu == 'Werte erfassen':  
        edit_values()     
    elif menu == 'Konfiguration editieren':
        edit_config()
    elif menu == 'Passwort ändern':
        change_password(session_state)
    elif menu == 'Verteiler verwalten':
        show_verteiler_verwalten()
    elif menu == 'Werte überprüfen':
        show_werte_ueberpruefen()
    elif menu == 'Versand Lagebericht':
        send_mail()
    elif st.sidebar.button('Ausführen'):        
        if menu == 'Lagebericht Mail versenden':
            send_mail()
        elif menu == 'Versand SMS':
            send_sms()
        elif menu == 'Versand Lagebericht':
            send_mail()
        elif menu == 'CH Zahlen einlesen':
            st.info('Prozess wurde gestartet')
            get_bs_cases(config)
            get_bl_cases(config)
            get_ch_cases(config)

def get_crypt_context():
    return CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=50000
    )

def is_valid_password(usr: str, pwd: str)->bool:
    """
    Passwörter werden gehasht in der DB abgelegt
    """
    context = get_crypt_context()
    sql = qry['get_usr_pwd'].format(usr)
    hashed_db_password = db.get_value(conn,sql)
    return context.verify(pwd, hashed_db_password)

def reset_password(session_state):
    sql = qry['user_info'].format(session_state.user_name)
    df = db.get_recordset(conn,sql)
    if len(df) > 0:
        mailadresse = df.iloc[0]['email']
        begruessung = df.iloc[0]['begruessung']
        subject = 'Das Passwort für die Covid-19 Lagebericht App wurde zurückgesetzt'
        pwd_neu = '{:07d}'.format(random.randint(0,999999))
        context = get_crypt_context()
        sql = qry['change_pwd'].format(context.hash(pwd_neu), session_state.user_name)
        if db.exec_non_query(conn, sql) == 1:
            if db.exec_non_query(conn, sql):
                text = f"""{begruessung},<br>dein Passwort wurde zurückgesetzt auf <br><b>{pwd_neu}</b><br>
                Bitte verwende nach dem ersten Login die Option `Passwort zurücksetzen` und setze dein eigenes Passwort.
                """
                sql = qry['send_reset_mail'].format(mailadresse,subject,text)
                if db.exec_non_query(conn, sql) == 1:
                    text = f"""{begruessung},<br>dein neues Passwort wurde an deine Mailadresse ({mailadresse}) geschickt. Bitte verwende nach dem ersten Login die
                    Menuoption `Passwort ändern`."""
                    st.markdown(text, unsafe_allow_html=True)
        else:
            st.warning('Beim reset des Passwortes gab es Probleme, kontaktieren sie den Systemadministrator')
    else:
        st.warning('Achte darauf, dass im Feld Benutzername dein Benutzerkürzel steht, z.B. sghxyz')

def log_entry(prozess_typ_id,result_id,fehlermeldung):
    cmd = qry["log_entry"].format(prozess_typ_id, session_state.user,result_id,fehlermeldung)
    db.exec_non_query(conn,cmd)

def show_login(session_state):
    st.write('## Login-Informationen')
    session_state.user_name = st.text_input('Benutzername', value = session_state.user_name)
    session_state.pwd = st.text_input('Passwort', value=session_state.pwd, type='password')
    col1, col2 = st.beta_columns((1,12))
    
    if col1.button('Login'):
        if is_valid_password(session_state.user_name, session_state.pwd):
            st.info('Willkommen beim Covid-Mailgenerator')
            session_state.logged_in = True
            sql = qry['user_info'].format(session_state.user_name)
            df = db.get_recordset(conn,sql)
            session_state.email = df.iloc[0]['email']
            session_state.user = df.iloc[0]['benutzer']
            log_entry(const.PROCESS['login'], const.RESULT_SUCCESS, '')
            st.experimental_rerun()
            show_menu(session_state)
        else:
            warning = 'Benutzername oder Passwort stimmen nicht'
            log_entry(const.PROCESS['login'], const.RESULT_ERROR, warning)
            st.warning(warning)

    if col2.button('Passwort zurücksetzen'):
        reset_password(session_state)

def display_app_info():
    """
    Zeigt die Applikations-Infos sowie Kontaktdaten bei Fragen in einer blauen box in der sidebar an.
    """
    
    logged_in_user = 'Benutzer: ' + session_state.user_name + '<br>' if session_state.user_name > '' else ''
    text = f"""
    <style>
        #appinfo {{
        font-size: 11px;
        background-color: lightblue;
        padding-top: 10px;
        padding-right: 10px;
        padding-bottom: 10px;
        padding-left: 10px;
        border-radius: 10px;
    }}
    </style>
    <div id ="appinfo">
    App-Version: {__version__} ({version_date})<br>
    Implementierung App: Statistisches Amt Basel-Stadt<br>
    DB-Server: {db.get_server_name(conn)}<br>{logged_in_user}
    Kontakt:<br>
    - <a href="{config['kontakt_fachlich']}">bei fachlichen Fragen</a><br>
    - <a href="{config['kontakt_technisch']}">bei technischen Fragen</a><br>
    </div>
    """

    st.sidebar.markdown(text, unsafe_allow_html=True)


def display_help():
    st.sidebar.markdown(f"### [📘]({const.URL_ANLEITUNG})")


def main():
    """Run this function to display the streamlit app"""
    
    # starting from version 71
    st.set_page_config(
        page_title="COVID-19 Lagebericht",
        # page_icon="🦠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    global menu_options
    global session_state 
    global config
    global df_config

    df_config, config = get_config()
    session_state = SessionState.get(user_name='', pwd = '', logged_in = False)
    st.markdown(STYLE, unsafe_allow_html=True)
    st.sidebar.markdown(f"### 🦠 COVID-19 Lagebericht-Cockpit")
    if session_state.logged_in:
        show_menu(session_state)
    else:
        show_login(session_state)
    display_app_info() 
    display_help()


main()