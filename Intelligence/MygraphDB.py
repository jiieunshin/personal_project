import neointerface
from neo4j import GraphDatabase
from py2neo import Graph
import pandas as pd
import re
from time import time
from datetime import datetime

class graphDB:
    def __init__(self, uri, user, password):
        """
        you must import 3 neo4j packages
        (1) neointerface 
            pip   : pip install neointerface
                    https://pypi.org/project/neointerface/
            github: https://github.com/GSK-Biostatistics/neointerface/tree/main
            
        (2) GraphDatabase
            pip   : pip install neo4j
                    https://neo4j.com/docs/api/python-driver/current/
            github: https://github.com/GSK-Biostatistics/neointerface/tree/main
            
        (3) py2neo 
            pip   : pip install py2neo
            github: https://pypi.org/project/py2neo/
        """

        self.neo = neointerface.NeoInterface(host=uri , credentials=(user, password))
        self.graph = Graph(uri, auth=(user, password))
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print("user :", user)
        print("current neo4j version :", self.neo.version())
        
    def close(self):
        self.neo.close()

    ###################
    ## 데이터 올리기 ##
    ###################
    
    # 올리려는 형태를 dataframe으로 맞추어야 함
    def add_node(self, entity, df):
        self.neo.load_df(df, label = node_label)
        query = f"""
            WITH apoc.date.currentTimestamp() AS outputInMs 
            MATCH (n:{entity}) RETURN id(n) as id, labels(n) as labels, properties(n) as property, outputInMs;
            """
        result = self.graph.run(query.format())
        df_result = pd.DataFrame(result)
        df_result.columns = result.keys()
        
        time_db = max(list(df_result['outputInMs']))-min(list(df_result['outputInMs']))
        
#         print("time elapsed in python: ", time_py)
        print("time elapsed in neo4j: ", time_db)
        return df_result
        
    def add_spo(self, entity, subject_id, object_id, predicate, video_id, properties = False):
    
#         # video id 조건 정리
#         vid_prop, vid_dicts = self.neo.dict_to_cypher(video_id)
#         vid_prop = vid_prop.replace("{", "")
#         vid_prop = vid_prop.replace("}", "")
#         vid_prop = vid_prop.replace("`", "")
#         vid_prop = vid_prop.replace(":", "=")

#         vid_prop = re.sub(r'\$par_(\d+)', lambda match: f"$v_prop{match.group(1)}", vid_prop)
#         vid_dicts = {f"v_prop{i+1}": value for i, value in enumerate(vid_dicts.values())}
        
#         # subject id 조건 정리
#         subj_prop, subj_dicts = self.neo.dict_to_cypher(subject_id)
#         subj_prop = subj_prop.replace("{", "")
#         subj_prop = subj_prop.replace("}", "")
#         subj_prop = subj_prop.replace("`", "")
#         subj_prop = subj_prop.replace(":", "=")
        
#         subj_prop = re.sub(r'\$par_(\d+)', lambda match: f"$s_prop{match.group(1)}", subj_prop)
#         subj_dicts = {f"s_prop{i+1}": value for i, value in enumerate(subj_dicts.values())}
        
#         # object id 조건 정리
#         obj_prop, obj_dicts = self.neo.dict_to_cypher(object_id)
#         obj_prop = obj_prop.replace("{", "")
#         obj_prop = obj_prop.replace("}", "")
#         obj_prop = obj_prop.replace("`", "")
#         obj_prop = obj_prop.replace(":", "=")

#         obj_prop = re.sub(r'\$par_(\d+)', lambda match: f"$o_prop{match.group(1)}", obj_prop)
#         obj_dicts = {f"o_prop{i+1}": value for i, value in enumerate(obj_dicts.values())}
        
#         cypher_rel_props, cypher_dict = self.neo.dict_to_cypher(properties)
#         cypher_rel_props = cypher_rel_props.replace('`', '')

#         # 파라미터 통합
#         cypher_dict = {**vid_dicts, **subj_dicts,** obj_dicts, **cypher_dict}

#         # 쿼리작성
#         q = f"""
#             MATCH (s:{node_label}), (o:{node_label}) 
#             WHERE s.{video_id} and o.{video_id} and s.{subj_prop} and o.{obj_prop} 
#             CREATE (s)-[r:`{predicate}`  {cypher_rel_props}]->(o)
#             RETURN id(r) as relationship_id, type(r) as type, properties(r) as relationshipProperty, id(startNode(r)) as startNodeId, properties(startNode(r)) as startNodeProperty, id(endNode(r)) as endNodeId, properties(endNode(r)) as endNodeProperty;
#             """
        if properties:
            cypher_rel_props, cypher_dict = self.neo.dict_to_cypher(properties)
            cypher_rel_props = cypher_rel_props.replace('`', '')
            cypher_dict = {**cypher_dict}
            # 쿼리작성
            q = f"""
                MATCH (s:{entity}), (o:{entity}) 
                WHERE s.video_id='{video_id}' and o.video_id='{video_id}' and s.object_id = {subject_id} and o.object_id = {object_id}
                CREATE (s)-[r:`{predicate}`  {cypher_rel_props}]->(o)
                RETURN id(r) as relationship_id, type(r) as type, properties(r) as relationshipProperty, id(startNode(r)) as startNodeId, properties(startNode(r)) as startNodeProperty, id(endNode(r)) as endNodeId, properties(endNode(r)) as endNodeProperty;
                """
            # 실행
            session = self.driver.session()
            result = session.run(q, cypher_dict)
            return pd.DataFrame(result.data())
        else:
            q = f"""
            MATCH (s:{entity}), (o:{entity}) 
            WHERE s.video_id='{video_id}' and o.video_id='{video_id}' and s.object_id = {subject_id} and o.object_id = {object_id}
            CREATE (s)-[r:`{predicate}`]->(o)
            RETURN id(r) as relationship_id, type(r) as type, properties(r) as relationshipProperty, id(startNode(r)) as startNodeId, properties(startNode(r)) as startNodeProperty, id(endNode(r)) as endNodeId, properties(endNode(r)) as endNodeProperty;
            """
            # 실행
            session = self.driver.session()
            result = session.run(q)
            return pd.DataFrame(result.data())
    
    ###############
    ## 전체 검색 ##
    ###############
    # 모든 nodel label 검색
    def get_node_list(self):
        def flatten(arg):
            ret = []
            for i in arg:
                ret.extend(i) if isinstance(i, list) else ret.append(i)
            return ret
    
        query = f"""
            MATCH (n) 
            RETURN distinct labels(n) as labels
            """
        session = self.driver.session()
        result = session.run(query)
        result = result.data()
        
        df_result = pd.DataFrame(result)
        out = list(df_result['labels'])
        out = flatten(out)
        return out
    
    def get_node_keyname(self, entity):
        start_time = time() * 1000
        query = f"""
            MATCH (n:{entity})
            UNWIND keys(n) as key
            RETURN distinct key as key
            """
        session = self.driver.session()
        result = session.run(query)
        df_result = pd.DataFrame(result)
        result = list(df_result[0])
        
        return result
        
    # 노드 내 모든 object 
    def get_node(self, entity = False, object = False,  criteria = False, video_id = True):
        """
        criteria: dictionary
        최종 출력형태: 리스트
        
        WITH apoc.date.currentTimestamp() AS outputInMs 
        MATCH (n:{node_label}) 
        RETURN id(n) as id, labels(n) as labels, properties(n) as property, outputInMs;
                        
        start_time = time() * 1000
        end_time = time() * 1000
        time_py = end_time - start_time            
        time_db = max(list(df_result['outputInMs']))-min(list(df_result['outputInMs']))
        print("time elapsed in python: ", time_py)
        print("time elapsed in neo4j: ", time_db)
                    .object
        """
        video_type = type(video_id)
        
        # 구문 생성
        # 1. match 구문
        if entity:
            q_match = f"MATCH (n:{entity}) "
        else:
            q_match = f"MATCH (n) "

        # 3. where 구문    
        if criteria:
            crit = criteria.split(',')
            for i, cr in enumerate(crit):
                cr = cr.replace(' ', '')
                if i == 0:
                    q_crit = f"n.object = '{cr}'"
                else:
                    q_crit = q_crit + f" or n.object = '{cr}' "
            q_crit = "(" + q_crit +")"
        else:
            q_crit = ''

        if object:
            obj = object.split(',')
            for i, ob in enumerate(obj):
                ob = ob.replace(' ', '')
                if i == 0:
                    q_obj = f"n.object = '{ob}'"
                else:
                    q_obj = q_obj + f" or n.object = '{ob}' "
            q_obj = "(" + q_obj +")"

        else:
            q_obj = ''

        if video_type == str:
            vd = video_id.split(',')
            for i, v in enumerate(vd):
                vd = vd.replace(' ', '')
                if i == 0:
                    q_vid = f"n.video_id = '{v}'"
                else:
                    q_vid = q_vid + f" or n.video_id = '{v}' "
            q_vid = "(" + q_vid +")"
        else:
            q_vid = ''
            
        if q_crit:
            if q_obj:
                if q_vid:
                    q_where = f"WHERE "+ q_crit +" and " + q_obj + " and " + q_vid + '\n'
                else:
                    q_where = f"WHERE "+ q_crit +" and " + q_obj + '\n'
            else:
                if q_vid:
                    q_where = f"WHERE "+ q_crit + " and " + q_vid + '\n'
                else:
                    q_where = f"WHERE "+ q_crit + '\n'
        else:
            if q_vid:
                q_where = f"WHERE "+ q_obj + " and " + q_vid + '\n'
            else:
                q_where = f"WHERE "+ q_obj + '\n'



        # 4. return 구문
        q_return = f"RETURN id(n) as id, labels(n) as entity, properties(n).object as object, n.video_id as video_id;"

        # 5. 전체 쿼리생성 및 실행
        query = q_match + '\n'+ q_where + '\n' + q_return
        
        session = self.driver.session()                    
        result = session.run(query)
        out = result.data()
        df_result = pd.DataFrame(out)   
        return df_result
    
    # relation
    def get_relation_keyname(self):
        query = f"""
            MATCH p=()-[r]->() 
            RETURN DISTINCT type(r)
            """
        session = self.driver.session()
        result = session.run(query)

        df_result = pd.DataFrame(result)
        results = list(df_result[0])

        return results

    def get_relationship(self, predicate = False, criteria = False, subject = False, object = False, link = False, video_id = True, print_relationprop = False):
        """        
        최종 출력형태: 데이터프레임
        보류중힌 함수: subject_prop = False, object_prop = False
        * `subject_prop` *dict* relationship의 subject로 추출할 조건 *(default = False)*
        * `object_prop` *dict* relationship의 object로 추출할 조건 *(default = False)*
        """
        
#         # 조건 정리
#         if criteria:
#             cypher_rel_props, cypher_dict = self.neo.dict_to_cypher(criteria)
#             cypher_rel_props = cypher_rel_props.replace('`', '') 
        
#         if type(subject_prop) == dict:        
#             subj_prop, subj_dicts = self.neo.dict_to_cypher(subject_prop)
#             subj_prop = subj_prop.replace("{", "")
#             subj_prop = subj_prop.replace("}", "")
#             subj_prop = subj_prop.replace("`", "")
#             subj_prop = subj_prop.replace(":", "=")

#             subj_prop = re.sub(r'\$par_(\d+)', lambda match: f"$s_prop{match.group(1)}", subj_prop)
#             subj_dicts = {f"s_prop{i+1}": value for i, value in enumerate(subj_dicts.values())}
        
#         if type(object_prop) == dict:
#             obj_prop, obj_dicts = self.neo.dict_to_cypher(object_prop)
#             obj_prop = obj_prop.replace("{", "")
#             obj_prop = obj_prop.replace("}", "")
#             obj_prop = obj_prop.replace("`", "")
#             obj_prop = obj_prop.replace(":", "=")

#             obj_prop = re.sub(r'\$par_(\d+)', lambda match: f"$o_prop{match.group(1)}", obj_prop)
#             obj_dicts = {f"o_prop{i+1}": value for i, value in enumerate(obj_dicts.values())}
        
        video_type = type(video_id)

        # 조건 정리
        if link == False:
            link = ''

        # 구문 생성
        # 1. match 구문
        if predicate:
            q_match = "MATCH p=()-[r:"+ predicate + "]->() "
        else:
            q_match = "MATCH p=()-[r]->() "

        # 2. with 구문
        q_with = "WITH *, properties(startNode(r)) as startNodeProperty, properties(endNode(r)) as endNodeProperty, properties(r) as RelationshipProperty"

        # 3. where 구문
        if subject and object == False:
            subj = subject.split(',')
            for i, sub in enumerate(subj):
                sub = sub.replace(' ', '')
                if i == 0:
                    sub_where = f"startNodeProperty.object = '{sub}' "
                else:
                    sub_where = sub_where + f" or startNodeProperty.object = '{sub}' "
            q_where = f"WHERE " + sub_where

        if subject == False and object:
            obj = object.split(',')
            for i, ob in enumerate(obj):
                ob = ob.replace(' ', '')
                if i == 0:
                    ob_where = f"endNodeProperty.object = '{ob}'"
                else:
                    ob_where = ob_where + f" or endNodeProperty.object = '{ob}' "
            q_where = f"WHERE " + ob_where

        if subject and object:
            subj = subject.split(',')
            for i, sub in enumerate(subj):
                sub = sub.replace(' ', '')
                if i == 0:
                    sub_where = f"startNodeProperty.object = '{sub}' "
                else:
                    sub_where = sub_where + f" or startNodeProperty.object = '{sub}' "

            obj = object.split(',')
            for i, ob in enumerate(obj):
                ob = ob.replace(' ', '')
                if i == 0:
                    ob_where = f"endNodeProperty.object = '{ob}'"
                else:
                    ob_where = ob_where + f" or endNodeProperty.object = '{ob}' "

            q_where = f"WHERE (" + sub_where + f") {link} (" + ob_where + ")"

        if subject == False and object == False:
            q_where = f''

        if type(video_id) == str:
            if q_where == '':
                q_where = f"WHERE startNodeProperty.video_id = '{video_id}' "
            else:
                q_where = q_where + f"startNodeProperty.video_id = '{video_id}' "

        if criteria:
            if q_where == '':
                q_where = f"WHERE r.{criteria} "
            else:
                q_where = q_where + f" and r.{criteria} "

        # 4. return 구문
        if print_relationprop:
            q_return = f"RETURN startNodeProperty.video_id as video_id, id(startNode(r)) as startNodeId, startNodeProperty.object as subject, id(r) as relationship_id, type(r) as predicate, id(endNode(r)) as endNodeId, endNodeProperty.object as object, RelationshipProperty;"
        else:
            q_return = f"RETURN startNodeProperty.video_id as video_id, id(startNode(r)) as startNodeId, startNodeProperty.object as subject, id(r) as relationship_id, type(r) as predicate, id(endNode(r)) as endNodeId, endNodeProperty.object as object, RelationshipProperty.begin_frame as begin_frame, RelationshipProperty.end_frame as end_frame;"
        # 5. 전체 쿼리생성 및 실행
        query = q_match + '\n'+ q_with + '\n'+ q_where + '\n' + q_return
        session = self.driver.session()                    
        result = session.run(query)
        out = result.data()
        df_result = pd.DataFrame(out)   
        return df_result

    def get_Digraph(self, type, objects, predicates):
        """
        함수명: get_graph
        input: get_node_num = 3
        """
        step = 2
        
        # 구문 생성
        # 1. match 구문
        if type == 'tree':
            def add_nodename(lst):
                return ["(n" + str(num) + ")" for num in lst]

            n_num = range(step+1)
            n_name = add_nodename(n_num)
            q_match1 = ", ".join(n_name)
            q_match1 = "MATCH " + q_match1
            
            a_step = step
            if a_step >= 1:
                q_match2 = f"(n0)-[r0]->(n1)"
            if a_step >= 2:
                a_step = a_step - 1
                for n in range(a_step):
                    q_match2 = q_match2 + f"-[r{n+1}]->(n{n+2})"
            q_match2 = "MATCH " + q_match2
        
        if type == 'center':
            q_match1 = f"(n0)"
            for n in range(step):
                q_match1 = q_match1 + f", (n{n+1}) "
            q_match1 = "MATCH " + q_match1
            a_step = step
            if a_step >= 1:
                q_match2 = f"(n0)-[r0]->(n1)"
            if a_step >= 2:
                a_step = a_step - 1
                for n in range(a_step):
                    q_match2 = q_match2 + f"<-[r{n+1}]-(n{n+2})"
            q_match2 = "MATCH " + q_match2
        
        # 2. with 구문
        def add_relename(lst):
            return ["properties(r" + str(num) + ") as RelationshipProperty" + str(num) for num in lst]

        n_num = range(step)
        n_name = add_relename(n_num)
        q_with = ", ".join(n_name)
        q_with = "WITH *, " + q_with

        # 3. where 구문
        obj_where = ''
        objs_split = ''
        if len(objects) == 0:
            obj_where = obj_where
        elif len(objects) >= 1:
            k = 0
            l = 0
            for objs in objects:
                k = k + 1
                if objs:
                    l = l + 1
                    if l >= 2:
                        obj_where = obj_where + " and "
                    objs_split = objs.split(',')
                    for i, obj in enumerate(objs_split):
                        obj = obj.replace(' ', '')
                        if i == 0:
                            obj_where = obj_where + "("
                            obj_where = obj_where + f"n{k-1}.object = '{obj}'"
                        else:
                            obj_where = obj_where + f" or n{k-1}.object = '{obj}'"
                    obj_where = obj_where + ")"


        pred_where = ''
        preds_split = ''
        if len(predicates) == 0:
            pred_where = pred_where
        elif len(predicates) >= 1:
            k = 0
            l = 0
            for preds in predicates:
                k = k + 1
                if preds:
                    l = l + 1
                    if l >= 2:
                        pred_where = pred_where + " and "
                    preds_split = preds.split(',')
                    for i, pred in enumerate(preds_split):
                        pred = pred.replace(' ', '')
                        if i == 0:
                            pred_where = pred_where + "("
                            pred_where = pred_where + f"type(r{k-1}) = '{pred}'"
                        else:
                            pred_where = pred_where + f" or type(r{k-1}) = '{pred}'"
                    pred_where = pred_where + ")"

        if len(objs_split) == 0 and len(objs_split) == 0:
            q_where = ''
        elif len(objs_split) >= 1 and len(preds_split) == 0:
            q_where = "WHERE " + obj_where 
        elif len(preds_split) >= 1 and len(objs_split) == 0:
            q_where = "WHERE " + pred_where
        elif len(preds_split) >= 1 and len(objs_split) >= 0:
            q_where = "WHERE " + obj_where + ' and ' + pred_where
     
        # 4. return 구문      
        q_return = ''
        for n in range(step):
            q_return = q_return + f"n{n}.object as object{n+1}, type(r{n}) as predicate{n+1}, RelationshipProperty{n}.begin_frame as begin_frame{n+1}, RelationshipProperty{n}.end_frame as end_frame{n+1}, "
        q_return = f"RETURN distinct n0.video_id as video_id, " + q_return + f"n{n+1}.object as object{n+2}"

        query = q_match1 + '\n'+ q_match2 + '\n'+ q_with + '\n'+ q_where + '\n' + q_return
        session = self.driver.session()                    
        result = session.run(query)
        out = result.data()
        df_result = pd.DataFrame(out)
        return df_result