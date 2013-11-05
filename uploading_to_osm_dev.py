import sqlite3 as lite
import sys
from pprint import pprint
import json
import urllib, urllib2
import OsmApi
from mylib import *
import random
import datetime

print 'python version=',sys.version

## declaring global variables
building_count = 0
surveyors_error = {}
new_building_not_found = 0
new_building = 0
overpass_api   = "http://overpass-api.de/api/interpreter?data="
con = None
con = lite.connect('../building_id/dev_db.db')
main_db = lite.connect('../building_id/main_pseudonumber_db - Copy.db')
# with con:
#     print con
    
#     main_cur = con.cursor()    
    # main_cur.execute('SELECT * from psuedonumber')
    # rows = main_cur.fetchall()

    # for row in rows:
    # 	print row

## Getting data from internet
print("Getting data from internet")
# formhub_request = urllib2.Request('https://formhub.org/nirabpudasaini/forms/fullexposure_form_new/api')
# try:
#     formhub_response = urllib2.urlopen(formhub_request)
#     print "successful"
# except urllib2.URLError:
#     print('We failed to reach a server.')
#     print('Reason: ', e.reason)
formhub_response = open('data_from_formhub_oct_29.json')

print "loading data"
json_data = json.loads(formhub_response.read())
json_data = convert(json_data)
# pprint(json_data)
# print type(json_data)

##OSMapi
MainApi = OsmApi.OsmApi(passwordfile = 'mainpassword')
DevApi = OsmApi.OsmApi(api='api06.dev.openstreetmap.org', passwordfile = 'devpassword',debug=True)
# dev_capabiliies = DevApi.Capabilities()
# print dev_capabiliies

##data entry
# DevApi.ChangesetCreate({'comment':u'full exposure survey','source':u'KathmanduLivingKLabs'})

for building in json_data:
    # pprint(building)
    print "\n building_count",building_count
    building_count+=1
    osm_id = None
    ##for debug
    print(building['_uuid'])
    #

    # if building exists query database and find out its id
    if(building['new_building']=="new_building_true"):  #
        
        building_id = building['building_id']   # get id in form
        
        #if real osmid is used
        if(len(building['building_id'])==9):    
            osm_id = building_id
            print "osm_id",osm_id

        #for pseudonumber connect to db and find number
        elif(len(building['building_id'])<=4):
            #need a function to convert formhub entries to database entries
            district = formhub_to_database_district(building.get('district'))
            vdc      = formhub_to_database_vdc(building.get('vdc'))
            ward     = formhub_to_database_ward(building.get('ward_no'))
            try:
                main_cur = main_db.cursor()   
                db_params = district,vdc,ward,building_id
                main_cur.execute("SELECT osmid from psuedonumber where district=? AND vdc=? AND ward=? AND new_id=?",db_params)
                db_response = convert(main_cur.fetchall())
                osm_id = db_response[0][0]
                print osm_id
            except Exception, e:
                print "surveyors error"
                print e
                surveyor_id = building['surveyor_id']
                surveyors_error.setdefault(surveyor_id,0)
                surveyors_error[surveyor_id] += 1

                # debug
                # raw_input()
                #
        else:
            pass

    # if it is new building
    elif(building['new_building'] == "new_building_false"):

        if 'area_id' in building:
            building_id = [building['area_id'], building['building_id']]
        else:
            building_id = [building['surveyor_id'],building['survey_date'][5:7],building['survey_date'][8:10],building['building_id']]
        
        # preparing overpass query
        overpass_tag     = {"kll:oid":"-".join(building_id)}
        overpass_query   = "[out:json];way[\"kll:oid\"="+"\""+overpass_tag['kll:oid']+"\"];"+"out ids;"
        print "overpass_query",overpass_query

        # correct request is like this: http://overpass-api.de/api/interpreter?data=%5Bout%3Ajson%5D%3Bway%5B%22kll%3Aoid%22%3D%224%2D10%2D07%2D21%22%5D%3B%0A
        overpass_request = overpass_api + urllib.quote(overpass_query)
        print "overpass_request",overpass_request
        try:
            overpass_response = json.loads(convert(urllib2.urlopen(overpass_request, timeout=60).read()))
            elements = overpass_response['elements']
            new_building += 1
            if(len(elements)):
                element  = elements[0]
                osm_id   = element['id']
                print "osm_id",osm_id
            else:
                new_building_not_found += 1
                print overpass_tag,"Not found"
                surveyor_id = building['surveyor_id']
                surveyors_error.setdefault(surveyor_id,0)
                surveyors_error[surveyor_id] += 1
        #for debug
                # raw_input("Press any Key")
        #
        except urllib2.HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
            if(e.code == 429):
                print "\n  Too Many Requests"
                raw_input("abort")
        except urllib2.URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason)


    #after id is determined
    # if(osm_id):
    #     print "retrieving data from main osm for way",osm_id
    #     old_data = convert(MainApi.WayFull(osm_id)

    #     if(not old_data['data']['tag']['building:structure']):
            
    #         #preserving old data
    #         new_data = {'tag':old_data['data']['tag']}
            
    #         #building ownership
    #         if(building["building_own"] == "building_own_rent"):
    #             new_data['tag']['building:ownership'] = "rent"
    #         else:
    #             new_data['tag']['building:ownership'] = "self"

    #         # building structural system
    #         if(building["building_struct"] == "building_struct_erc"):
    #             new_data['tag']["building:structure"] = "engineered_reinforced_concrete"
    #         elif(building["building_struct"] == "building_struct_nrc"):
    #             new_data['tag']["building:structure"] = "non_engineered_reinforced_concrete"
    #         elif(building["building_struct"] == "building_struct_sc"):
    #             new_data['tag']["building:structure"] = "load_bearing_stone_wall_in_cement_mortar"
    #         elif(building["building_struct"] == "building_struct_bls"):
    #             new_data['tag']["building:structure"] = "load_bearing_brick_wall_in_lime_surkhi_mortar"
    #         elif(building["building_struct"] == "building_struct_bc"):
    #             new_data['tag']["building:structure"] = "load_bearing_brick_wall_in_cement_mortar"
    #         elif(building["building_struct"] == "building_struct_bm"):
    #             new_data['tag']["building:structure"] = "load_bearing_brick_wall_in_mud_mortar"
    #         elif(building["building_struct"] == "building_struct_dsm"):
    #             new_data['tag']["building:structure"] = "load_bearing_dry_stone_wall"
    #         elif(building["building_struct"] == "building_struct_sm"):
    #             new_data['tag']["building:structure"] = "load_bearing_stone_wall_in_mud_mortar"
    #         elif(building["building_struct"] == "building_struct_ad"):
    #             new_data['tag']["building:structure"] = "adobe"

    #         # no of stories
    #         if(building["building_stories"]):
    #             new_data['tag']['building:levels'] = building["building_stories"]

    #         # building use
    #         if(building["building_use"] == "building_use_res"):
    #             new_data['tag']['building:use'] = 'residential'
    #         elif(building["building_use"] == "building_use_edu"):
    #             new_data['tag']['building:use'] = 'education'
    #         elif(building["building_use"] == "building_use_hel"):
    #             new_data['tag']['building:use'] = 'health'
    #         elif(building["building_use"] == "building_use_com"):
    #             new_data['tag']['building:use'] = 'commercial'
    #         elif(building["building_use"] == "building_use_res"):
    #             new_data['tag']['building:use'] = 'residential'

    #         # floor material type
    #         if(building["building_flt"] == "building_flt_rig"):
    #             new_data['tag']['floor:material:type'] = 'rigid'
    #         elif(building["building_flt"] == "building_flt_fle"):
    #             new_data['tag']['floor:material:type'] = 'flexible'

    #         # roof material type
    #         if(building["building_rft"] == "building_rft_rig"):
    #             new_data['tag']['roof:material:type'] = 'rigid'
    #         elif(building["building_rft"] == "building_rft_fle"):
    #             new_data['tag']['roof:material:type'] = 'flexible'

    #         # building attachment
    #         if(building["building_attach"] == "building_attach_true"):
    #             new_data['tag']['building:adjacency'] = "yes"
    #         elif(building["building_attach"] == "building_attach_false"):
    #             new_data['tag']['building:adjacency'] = "no"

    #         # shape in plan
    #         if(building["building_shape_plan"] == "building_shape_plan_r"):
    #             new_data['tag']['shape:plan'] = "regular"
    #         elif(building["building_shape_plan"] == "building_shape_plan_r"):
    #             new_data['tag']['shape:plan'] = "irregular"

    #         # shape in elevation
    #         if(building["building_shape_elev"] == "building_shape_elev_r"):
    #             new_data['tag']['shape:elevation'] = "regular"
    #         elif(building["building_shape_elev"] == "building_shape_elev_ir"):
    #             new_data['tag']['shape:elevation'] = "irregular"
    #         elif(building["building_shape_elev"] == "building_shape_elev_nt"):
    #             new_data['tag']['shape:elevation'] = "narrow_tall"
    #         elif(building["building_shape_elev"] == "building_shape_elev_ntir"):
    #             new_data['tag']['shape:elevation'] = "narrow_tall_irregular"

    #         # visible physical condition
    #         if(building["building:condition"] == "building_condition_poor"):
    #             new_data['tag']['physical_condition'] = "poor"
    #         elif(building["building:condition"] == "building_condition_avg"):
    #             new_data['tag']['physical_condition'] = "average"
    #         elif(building["building:condition"] == "building_condition_good"):
    #             new_data['tag']['physical_condition'] = "good"

    #         # building overhang
    #         if(building["building_overhang"]=="building_overhang_false"):
    #             new_data['tag']['building:overhang'] = 'no'
    #         elif(building["building_overhang"]=="building_overhang_true"):
    #             new_data['tag']['building:overhang'] = 'yes'

    #         # building soft storey
    #         if(building["building_softstor"]=="building_softstor_false"):
    #             new_data['tag']['building:soft_storey'] = 'no'
    #         elif(building["building_softstor"]=="building_softstor_true"):
    #             new_data['tag']['building:soft_storey'] = 'yes'

    #         # building gable wall
    #         if(building["building_gable"]=="building_gable_false"):
    #             new_data['tag']['building:gable_wall'] = 'no'
    #         elif(building["building_gable"]=="building_gable_true"):
    #             new_data['tag']['building:gable_wall'] = 'yes'

    #     else:
    #         print "Data exists for way",osmid

    #     print DevApi.NodeCreate(new_data)
    # #
# DevApi.ChangesetClose()

print "No of buildings",building_count
print "surveyors_error",surveyors_error
print "new_building",new_building
print "new_building_not_found",new_building_not_found