import requests, json, tweepy
import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

from pytrends.request import TrendReq

def form(request):
    """Front - Formulario para petición"""
    return render(request, 'form.html')

def api_call(request, variable_set):
    current_date = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    # Leyendo el archivo
    f = open('google_response.json', 'r')
    # Extrayendo el json
    json_file = json.loads(f.read())
    json_file_datetime = json_file['captured_time']

    fmt = '%Y-%m-%d %H:%M:%S'
    tstamp1 = datetime.datetime.strptime(json_file_datetime, fmt)
    tstamp2 = datetime.datetime.strptime(current_date, fmt)

    if tstamp1 > tstamp2:
        td = tstamp1 - tstamp2
    else:
        td = tstamp2 - tstamp1
    td_mins = int(round(td.total_seconds() / 60))
    if td_mins >= settings.MAX_TIME:
        # print('-----------------')
        # print(variable_set)
        # print('-----------------')
        """Back - Peticion a google trends"""
        class Busqueda(object):
            pass
        
        busquedas = []
        
        pytrends    = TrendReq(hl='es-MX')
        
        # all_keywords = [
        #     'Cloralex',
        # ]
        # all_keywords = [
        #     'Suavizante Ensueño',
        #     'Suavitel'
        # ]
        all_keywords = [
            'Pinol',
            'Fabuloso'
        ]
        # comparacion_kw = [
        #     'Cloralex',
        #     'Clorox'
        # ]
        # comparacion_kw = [
        #     'Suavizante Ensueño',
        #     'Suavitel'
        # ]   
        comparacion_kw = [
            'Pinol',
            'Fabuloso'
        ]        
        keywords     = []
        cat         = 0
        
        countries = ['mexico']
        
        trending_topics = []
        
        def trending_searches(country):
            data = pytrends.trending_searches(country)
            data = data.to_json()
            data = json.loads(data)
            nueva_busqueda = {
                "pais":country,
                "lo_mas_buscado":data
            }
            return nueva_busqueda
            
        for country in countries:
            # print(country)
            trending_topics.append(trending_searches(country))
        
        def rel_queries():
            busquedas = []
            # Busquedas relacionadas de los ultimos 3 meses
            pytrends.build_payload(
                all_keywords,
                cat,
                timeframe='today 3-m',
                geo='MX',
                gprop=''
            )
            
            data = pytrends.related_queries()
            for kw in all_keywords:
                # nueva_busqueda = Busqueda()
                # print('')
                # print('Top de busquedas en relacion a "'+kw+'":')
                # print(data[kw]['top'].head())
                top_busquedas = {}
                try:
                    top_busquedas = data[kw]['top'].head()
                    top_busquedas = top_busquedas.to_json()
                    top_busquedas = json.loads(top_busquedas)
                except:
                    print('An exception occurred')
                
                nueva_busqueda = {
                    "kw":kw,
                    "top_busquedas":top_busquedas
                }
                # nueva_busqueda.top_busquedas = top_busquedas
                busquedas.append(nueva_busqueda)
                
            return busquedas
            
        busquedas_relacionadas = rel_queries()
        
        def interest_per_region():
            # Compara las keyword, les pone una calificacion por estado/pais
            pytrends.build_payload(
                comparacion_kw,
                cat,
                timeframe='today 5-y',
                geo='MX',
                gprop=''
            )
            
            data = pytrends.interest_by_region(
                        resolution = 'COUNTRY',
                        inc_low_vol = True,
                        inc_geo_code = True
                    )
            
            # for kw in all_keywords:
            #     print(kw)
            #     data = data.sort_values(by = kw, ascending = False)
            #     print(data.head())
            #     print('')
            
            return data
            
        interes_por_region = interest_per_region().to_json()
        interes_por_region = json.loads(interes_por_region)
        
        def check_trends():
            
            busqueda = Busqueda()
            
            pytrends.build_payload(
                keywords,
                cat,
                timeframe='today 5-y',
                geo='',
                gprop=''
            )
            
            data            = pytrends.interest_over_time()
            # Cual fue el nivel de interes en los ultimos 12 meses
            # Datos crudos para utilizar en grafica
            datos_crudos = data.to_json()
            datos_crudos = json.loads(datos_crudos)
            mean            = round(data.mean(), 2)
            # Como se compara con el ultimo año
            avg_last_year   = round( data[kw][-52:].mean(), 2 )
            # Como se compara el ultimo año con el primero de hace 12 meses
            avg_first_year  = round( data[kw][:52].mean(), 2 )
            trend_last_year = round( ( (avg_last_year/mean[kw]) - 1 ) * 100, 2)
            trend_first_year= round( ( (avg_last_year/avg_first_year) - 1 ) * 100, 2)
            
            
            # print('El promedio en 5 años de interés en ' + kw + ' fué de ' + str(mean[kw]) + '.')
            busqueda.promedio_total = 'El promedio en 5 años de interés en ' + kw + ' fué de ' + str(mean[kw]) + '.'
            # print('El ultimo año, el interes en ' + kw + ' en comparación a'
            #   + ' los ultimos 5 años ha cambiado un ' + str(trend_last_year) +'%')
            busqueda.interes = 'El ultimo año, el interes en ' + kw + ' en comparación a' + ' los ultimos 5 años ha cambiado un ' + str(trend_last_year) +'%'
            
            # Tendencia estable
            if mean[kw] > 75 and abs(trend_last_year) <= 5:
                # print('El interes por ' + kw + 'ha sido estable en los ultimos 5 años.')
                busqueda.estabilidad = 'El interes por ' + kw + 'ha sido estable en los ultimos 5 años.'
            elif mean[kw] > 75 and trend_last_year >  5:
                # print('El interes por ' + kw + 'ha sido estable y aumentó en los ultimos 5 años.')
                busqueda.estabilidad = 'El interes por ' + kw + 'ha sido estable y aumentó en los ultimos 5 años.'
            elif mean[kw] > 75 and trend_last_year < -5:
                # print('El interes por ' + kw + 'ha sido estable y decreció en los ultimos 5 años.')        
                busqueda.estabilidad = 'El interes por ' + kw + 'ha sido estable y decreció en los ultimos 5 años.'
                
            # Relativamente estable
            elif mean[kw] > 60 and abs(trend_last_year) <= 15:
                # print('El interes por ' + kw + 'ha sido relativamente estable en los ultimos 5 años.')
                busqueda.estabilidad = 'El interes por ' + kw + 'ha sido relativamente estable en los ultimos 5 años.'
            elif mean[kw] > 60 and trend_last_year >  15:
                # print('El interes por ' + kw + 'ha sido relativamente estable y aumentó en los ultimos 5 años.')        
                busqueda.estabilidad = 'El interes por ' + kw + 'ha sido relativamente estable y aumentó en los ultimos 5 años.'
            elif mean[kw] > 60 and trend_last_year < -15:
                # print('El interes por ' + kw + 'ha sido relativamente estable y decreció en los ultimos 5 años.')        
                busqueda.estabilidad = 'El interes por ' + kw + 'ha sido relativamente estable y decreció en los ultimos 5 años.'
            
            # Temporal
            elif mean[kw] > 20 and abs(trend_last_year) <= 15:
                # print('El interes por ' + kw + ' es temporal.')
                busqueda.estabilidad = 'El interes por ' + kw + ' es temporal.'
            
            # Nueva tendencia
            elif mean[kw] > 20 and trend_last_year > 15:
                # print('El interes por ' + kw + ' es tendencia.')
                busqueda.estabilidad = 'El interes por ' + kw + ' es tendencia.'
                
            # Tendencia en declive
            elif mean[kw] > 20 and trend_last_year < -15:
                # print('El interes por ' + kw + '  está perdiendose significativamente.')
                busqueda.estabilidad = 'El interes por ' + kw + '  está perdiendose significativamente.'
                
            # Nuevo y en tendencia
            elif mean[kw] > 0 and trend_last_year > 15:
                # print('El interes por ' + kw + ' es nuevo y tendencia.')
                busqueda.estabilidad = 'El interes por ' + kw + ' es nuevo y tendencia.'
            
            # Declive
            elif mean[kw] > 0 and trend_last_year < -15:
                # print('El interes por ' + kw + ' esta en declive y no es comparable a su pico.')
                busqueda.estabilidad = 'El interes por ' + kw + ' esta en declive y no es comparable a su pico.'
            
            # Otro
            else:
                # print("Esto es algo que deberia revisarse.")
                busqueda.estabilidad = "Esto es algo que deberia revisarse."
                
            # Comparacion del ultimo año vs hace 5 años
            if avg_first_year == 0:
                # print('Esto no existia hace 5 años.')
                busqueda.comparacion = 'Esto no existia hace 5 años.'
            elif trend_first_year > 15:
                # print('El interes en el ultimo año ha sido bastante alto comparado a hace 5 años.'
                    #   + ' Se ha incrementado por ' + str(trend_first_year) + '%.')
                busqueda.comparacion = 'El interes en el ultimo año ha sido bastante alto comparado a hace 5 años.' + ' Se ha incrementado por ' + str(trend_first_year) + '%.'
            elif trend_first_year < 15:
                # print('El interes en el ultimo año ha sido bastante bajo comparado a hace 5 años.'
                    #   + ' Se ha reducido por ' + str(trend_first_year) + '%.')
                busqueda.comparacion = 'El interes en el ultimo año ha sido bastante bajo comparado a hace 5 años.' + ' Se ha reducido por ' + str(trend_first_year) + '%.'
            else:
                # print('El interes en el ultimo año ha sido comparable a hace 5 años.'
                    #   + ' Ha cambiado por ' + str(trend_first_year) + '%.')
                busqueda.comparacion = 'El interes en el ultimo año ha sido comparable a hace 5 años.' + ' Ha cambiado por ' + str(trend_first_year) + '%.'

            nueva_busqueda = {
                "busqueda":kw,
                "promedio_total":busqueda.promedio_total,
                "interes":busqueda.interes,
                "estabilidad":busqueda.estabilidad,
                "comparacion":busqueda.comparacion,
                "datos_crudos":datos_crudos
            }
            busquedas.append(nueva_busqueda)
            # print('')
        for kw in comparacion_kw:
            keywords.append(kw)
            check_trends()
            keywords.pop()
        
        
        response = {
            'captured_time': current_date,
            'msg': 'success',
            'lo_mas_buscado_por_pais':trending_topics,
            'analisis':busquedas,
            'interes_por_region':interes_por_region,
            'busquedas_relacionadas':busquedas_relacionadas
        }
        # print(busquedas)
        f = open('google_response.json', 'w')
        f.write(json.dumps(response))
        f.close()
    else:
        response = json_file
    return JsonResponse(response)

def tw_api_call(request):
    current_date = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    # Leyendo el archivo
    f = open('twitter_response.json', 'r')
    # Extrayendo el json
    json_file = json.loads(f.read())
    json_file_datetime = json_file['captured_time']

    fmt = '%Y-%m-%d %H:%M:%S'
    tstamp1 = datetime.datetime.strptime(json_file_datetime, fmt)
    tstamp2 = datetime.datetime.strptime(current_date, fmt)

    if tstamp1 > tstamp2:
        td = tstamp1 - tstamp2
    else:
        td = tstamp2 - tstamp1
    td_mins = int(round(td.total_seconds() / 60))
    if td_mins >= settings.MAX_TIME:
        # Ya han pasado al menos 15 minutos, nueva petición
        consumer_key        = "JOPFYmrDvgLwEtrSVCnqwwwyq"
        consumer_secret     = "Ab0CbdtXqWZtIluE48qZaXJwJxaAdduIqtOMWYOkbVLTPQ4CNv"
        access_token        = "1496939578208440328-66cw5MgJoGRYKQyKvvGUxNWdfrlHVt"
        access_token_secret = "gcZRxFl5GR37faXq6S6ZmMtEqnj5V1TOCmPhsUoA4LtQy"

        auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth, wait_on_rate_limit=True)

        # ***** Buscar detalles de un perfil especifico *****
        # ***** profile = api.get_user(screen_name='john5guitarist') *****

        # ***** Buscar codigos de país para luego obtener trends *****
        # world_list = api.available_trends()

        # ***** Buscar trends de cierto codigo de país *****
        trends      = api.get_place_trends(116545)
        trends_mty  = api.get_place_trends(134047)
        trends_gdl  = api.get_place_trends(124162)
        trends_acl  = api.get_place_trends(111579)
        trends_chi  = api.get_place_trends(115958)
        response    = {
            'captured_time': current_date,
            'platform':'Twitter',
            'msg': 'success',
            'trends_principales_ciudades':{
                'trends_cdmx':trends,
                'trends_mty':trends_mty,
                'trends_gdl':trends_gdl,
                'trends_acl':trends_acl,
                'trends_chi':trends_chi,
            },
            # 'world_list': world_list
        }
        f = open('twitter_response.json', 'w')
        f.write(json.dumps(response))
        f.close()

    else:
        response = json_file
        
    return JsonResponse(response)


def switch(opt):
        options = {
            "set1":set1(),
            "set2":set2(),
            "set3":set3()
        }
        return options.get(opt, "Ignore")

def set1():
    return {
        'keywords':[
            'Cloralex',
            'Clorox'
        ]
    }
def set2():
    return {
        'keywords':[
            'Pinol',
            'Fabuloso'
        ]
    }
        
def set3():
    return {
        'keywords':[
            'Suavizante Ensueño',
            'Suavitel'
        ]
    }