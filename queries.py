qry = {'log_today': """
    SELECT convert(varchar(20), [datum], 104) as tag
      ,format([datum], 'HH:mm') as zeit
      ,[Prozess]
      ,[Resultat]
      ,[fehlermeldung]
      ,[verantwortlich]
    FROM [dbo].[v_log]
    where convert(date,datum) > convert(date,getdate() - 2)
    order by datum desc
    """,
    'run_update': "exec [dbo].[sp03_zeitreihe_update]",
    'inzidenzen_qs': "select * from dbo.v_qs_inzidenzen",
    'send_test_mail': "exec [dbo].[sp07_send_mail] @version=3, @an='{}'",
    'send_mail': "exec [dbo].[sp07_send_mail] @version=4",
    'send_sms': "exec [dbo].[sp08_send_sms] @version=4",
    'send_test_sms': "exec [dbo].[sp08_send_sms] @version=3, @an='{}'",
    'show_config': 'select [schluessel],[wert],[Beschreibung] from [dbo].[v_konfiguration] order by schluessel',
    'show_bl_cases': """SELECT top 20 
        convert(varchar(20),datum,104) as tag
        ,[faelle_bl_kum]
        from [dbo].[zeitreihe_publikation]
        where [faelle_bl_kum] is not null
        order by datum desc
    """,
    'show_bs_hospitalised': """SELECT top 20 
        convert(varchar(20),datum,104) as tag
        ,[hospitalisierte_total], [hospitalisierte_bs], [hospitalisierte_icu] as [hospitalisierte_IS],
        case when hosp_data_komplett = 1 then 'komplett' else 'unvollständig' end as [Daten komplett]
        from [dbo].[zeitreihe_publikation]
        where [hospitalisierte_bs] is not null
        order by datum desc
    """,
    'show_ch_faelle': """SELECT top 20 
        convert(varchar(20),datum,104) as tag
        ,[faelle_ch_kum]
        from [dbo].[zeitreihe_publikation]
        where [faelle_ch_kum] is not null
        order by datum desc
    """,
    'compare_values':"""
        SELECT 
        [Feld]
        ,[heute]
        ,[gestern]
        ,[differenz]
        ,[diff_pzt]
        FROM [dbo].[v_vergleich_heute_gestern]
        order by [row_id]
    """,

    'manual_update': """update zeitreihe_publikation set inzidenz07_loerrach = {}, inzidenz07_haut_rhin = {}, [isoliert_aph_bs] = {}
        from zeitreihe_publikation
        where convert(date,datum) = '{}'
    """,
    'get_manual_edit_fields': """Select [inzidenz07_loerrach], [inzidenz07_haut_rhin], [isoliert_aph_bs] from zeitreihe_publikation
            where convert(date,datum) = '{}'
    """,
    'edit_values_view': """Select convert(varchar(20),Datum, 104) as Tag, isoliert_aph_bs as [Isolierte in APH], inzidenz07_loerrach as [7-Tage Inzidenz Lörrach]
        , inzidenz07_haut_rhin as [7-Tage Inzidenz Haut-Rhin] 
        from [dbo].[zeitreihe_publikation]
        order by Datum desc
    """,
    'import_file':"""execute [lagebericht_app].[dbo].[sp02_lagebericht_extract]
    """,
    'export_ogd_nach_test_datum': """Select * from dbo.v_faelle_nach_test_datum order by datum desc
    """,
    'export_ogd_nach_publikations_datum': """Select * from dbo.v_faelle_nach_publikations_datum order by datum desc
    """,
    'export_ogd_detail': """select * from [lagebericht_app].[dbo].[v_covid_faelle_bs] 
		order by [test_datum], pers_alter, geschlecht
    """,
    'export_ogd_nach_gemeinden': """Select * from dbo.v_faelle_nach_gemeinden order by datum desc
    """,
    'get_konfig': """Select * from dbo.v_konfiguration order by schluessel
    """,
    'update_config': """update dbo.konfiguration set wert = {} where schluessel = '{}'
    """,
    'update_faelle_bl': "update [dbo].[zeitreihe_publikation] set [faelle_bl_kum] = {} where convert(date,datum ) = convert(date,'{}');",
    'update_faelle_bs': """update [dbo].[zeitreihe_publikation] set [hospitalisierte_bs] = {}, hospitalisierte_total = {}, hospitalisierte_icu = {} 
        , hosp_data_komplett = {} where convert(date,datum ) = convert(date,'{}');
    """,
    'update_faelle_ch': "update [dbo].[zeitreihe_publikation] set [faelle_ch_kum] = {} where convert(date,datum ) = convert(date,'{}');",
    'get_usr_pwd': "select passwort as result from dbo.benutzer where benutzer = '{}'",
    'rowcount_lagebericht_today': "SELECT count(*) as result FROM [lagebericht_app].[dbo].[lagebericht] where convert(date,[time_stamp]) = convert(date,getdate())",
    'truncate_rohdaten': "truncate table [lagebericht_app].[dbo].[lagebericht_roh]",
    'insert_roh_to_lagebericht': "exec [dbo].[sp02b_update_rohdaten]", 
    'get_html_table': "EXEC	[dbo].[make_html_table] @table_name = N'{}'",
    'save_reporting_time': "update [dbo].[zeitreihe_publikation] set meldezeit = '{}' where convert(date,datum) = convert(date,getdate()) and meldezeit is null",
    'change_pwd': "update [dbo].[benutzer] set passwort = '{}' where benutzer = '{}' ",
    'user_info': "select * from dbo.v_benutzer where benutzer = '{}'",
    'send_reset_mail': """
    EXEC msdb.dbo.sp_send_dbmail 
	@profile_name    = 'default', 
	@recipients      = '{}',
	@from_address    = 'epi@bs.ch',
	@subject         = '{}',
	@body            = '{}',
	@body_format     = 'HTML'
    """,
    'person_all': "select * from v_personen order by name",
    'person_list': "select id, nachname + ' ' + vorname as name from person order by nachname, vorname",
    'person_info': "select * from person where id = {}",
    'person_update': """UPDATE [dbo].[person]
    SET [nachname] = '{}'
      ,[vorname] = '{}'
      ,[email] = '{}'
      ,[mobile] = '{}'
      ,[ist_benutzer] = '{}'
    WHERE id = {}
    """,
    'person_delete': "DELETE FROM [dbo].[person] WHERE id = {}",
    'person_new': """insert into [dbo].[person] (nachname, vorname, email, mobile) 
        values('<nachname>', '<vorname>', '<email>', '<mobile>')""",
    'lookup_code_list': """SELECT [id]
      ,[name]
    FROM [lagebericht_app].[dbo].[lookup_code]  
    where kategorie_id = {}
    order by order_id, [name]""",
    'verteiler_person_bez': "select * from dbo.person_verteiler_bez where verteiler_id = {}",
    'verteiler_person_empty': "delete from dbo.person_verteiler_bez where verteiler_id = {}",
    'verteiler_person_insert': "insert into dbo.person_verteiler_bez (person_id, verteiler_id) values ({},{})",
    'check_values_table': """SELECT convert(date, datum) as [datum], {}
        FROM [lagebericht_app].[dbo].[zeitreihe_publikation]
        order by datum desc 
    """, 
    'check_values_plot': """SELECT date, {}
        FROM [lagebericht_app].[dbo].[zeitreihe_publikation]
        order by datum desc 
    """, 
    'insert_lagebericht': """delete from lagebericht where convert(date, time_stamp) = convert(date, getdate());
		insert into lagebericht ({}) select {} from dbo.lagebericht_roh;
        insert into [dbo].[lagebericht_log] ([prozess_typ_id],[result_id]) values(1,5);
    """,
    'synch_person_list': "execute [dbo].[sp09_personen_aktualisieren]",
    'verstorbene': """SELECT convert(date,[datum],104) as tag
      ,id as patient_id
      ,[geschlecht]
      ,[pers_alter]
      ,[vorerkrankung]
    FROM [dbo].[v_gestorbene]
    order by datum desc""",

    "inzidenzen": """SELECT datum, {}
        FROM [dbo].[v_inzidenzen]
        order by datum desc""",
    "add_today_record": "execute [dbo].[sp_records_publikation_ergaenzen]",
    "db_fields":"select field_name, db_field_name from dbo.felder where import = 1",
    "log_entry": """insert into [dbo].[lagebericht_log] ([prozess_typ_id],[verantwortlich],[result_id],[fehlermeldung])
		values({},'{}',{},'{}')
    """,
    "meldezeit_today": """SELECT [meldezeit] as result FROM [dbo].[zeitreihe_publikation]
    where convert(date,datum) = convert(date,getdate())""",
    "update_meldezeit": """UPDATE [dbo].[zeitreihe_publikation] set meldezeit = '{}'  
    where convert(date,datum) = convert(date,getdate())""",
    "mail_comment_today": """SELECT coalesce([mail_kommentar],'') as result FROM [dbo].[zeitreihe_publikation]
        where convert(date,datum) = convert(date,getdate())""",
    "update_mail_comment": """UPDATE [dbo].[zeitreihe_publikation] set mail_kommentar = '{}'  
        where convert(date,datum) = convert(date,getdate())""",
    "delete_hosp_data_today": """update [dbo].[zeitreihe_publikation] set 
        [hospitalisierte_bs] = null
    ,[hospitalisierte_total] = null
    ,[hospitalisierte_icu] = null
    where convert(date,datum)=getdate()""",
    
    "plot_data": """SELECT [datum]
      ,[faelle_bs]
      ,[faelle_bs_kum]
      ,[mittel_07_tage_bs]
  FROM [dbo].[v_faelle_nach_test_datum] 
  where datum < convert(date, getdate())
  order by datum"""
}