import pandas as pd
import re
import time
# from datetime import datetime
import neointerface
from neo4j import GraphDatabase
from py2neo import Graph

###################
## 1. connection ##
###################
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
        
        q = "CALL dbms.components() YIELD name, versions"
        session = self.driver.session()
        result = session.run(q)
        
        print("-- Successfully connected! --")
        print("connection user name :", user)
        print("current neo4j version ", result.data()[0]['versions'][0])
        
        
    def close(self):
        self.neo.close()

    ###############
    ## 2. create ##
    ###############
    def add_object(self, df):
        """
        Upload a objects to Neo4j"
        
        :param df:  a pandas DataFrame with information for objects
        """
        
        start_time = time.time()
        result = self.neo.load_df(df, label = 'object')
        end_time = time.time()

        print("total time elapsed: ", end_time-start_time)
        print( )
        print(f"Load the {df.shape[0]} objects successfully.")
    
    def add_spo(self, df):
        """
        Upload a triple (subject-predicate-object) to Neo4j
        
        :param df:  a pandas DataFrame with information for spo
        """

        session = self.driver.session()
        def add_sub_spo(self, video_id, subject, object, predicate, properties):
            cypher_rel_props, cypher_dict = self.neo.dict_to_cypher(properties)
            cypher_rel_props = cypher_rel_props.replace('`', '')
            cypher_dict = {**cypher_dict}
            # 쿼리작성
            q = f"""
                MATCH (s:object), (o:object) 
                WHERE s.video_id='{video_id}' and o.video_id='{video_id}' and s.object = '{subject}' and o.object = '{object}'
                CREATE (s)-[r:`{predicate}`  {cypher_rel_props}]->(o)
                RETURN s.video_id as video_id, s.video_path as video_path, properties(r).begin_frame as begin_frame, properties(r).end_frame as end_frame, properties(r).captions as captions, s.object as subject, type(r) as predicate, o.object as object;
                """
            # 실행
            result = session.run(q, cypher_dict)
            return result.data()

        start_time = time.time()
        for i, row in df.iterrows():
            prop = row[['video_id', 'video_path', 'begin_frame', 'end_frame', 'captions']].to_dict()
            add_sub_spo(self, video_id = row['video_id'], subject = row['subject'], object = row['object'], predicate = row['predicate'], properties = prop )
        end_time = time.time()
        
        print("total time elapsed: ", end_time-start_time)
        print( )
        print(f"Load the {df.shape[0]} spos successfully.")
        
    ################
    ##  3. search ##
    ################
    def get_description(self):
        """
        A function that displays the information of currently stored objects and predicates in Neo4j. 
        It outputs the average, minimum, and maximum counts of objects and predicates, among other statistics.
        """
        
        ## first: count of nodes and relationships in DB ##
        query = f"""
            MATCH (n)
            RETURN count(n) as node_count
            """
        session = self.driver.session()
        result = session.run(query)
        result = result.data()
        df_result1 = pd.DataFrame(result)
    
        query = f"""
            MATCH ()-->() RETURN count(*) as relationship_count; 
            """
        session = self.driver.session()
        result = session.run(query)
        result = result.data()
        df_result2 = pd.DataFrame(result)
        out1 = pd.concat([df_result1, df_result2], axis=1)

        ## second: information in DB ##
        ## What kind of nodes exist
        ## Sample some nodes, reporting on property and relationship counts per node.
        query = f"""
            MATCH (n) WHERE rand() <= 0.1
            RETURN
            DISTINCT labels(n) as node_label,
            count(*) AS SampleSize,
            avg(size(keys(n))) as Avg_PropertyCount,
            min(size(keys(n))) as Min_PropertyCount,
            max(size(keys(n))) as Max_PropertyCount,
            avg(size( (n)-[]-() ) ) as Avg_RelationshipCount,
            min(size( (n)-[]-() ) ) as Min_RelationshipCount,
            max(size( (n)-[]-() ) ) as Max_RelationshipCount
            """
        session = self.driver.session()
        result = session.run(query)
        result = result.data()
        out2 = pd.DataFrame(result)
        
        print('----node and relation count----')
        print(out1)
        print('\n')
        print('----Information for property and relationship----')
        print(out2)
        return out1, out2
                
    # 모든 nodel label 검색
    def get_object_list(self):
        """
        A function that outputs a unique list of objects stored in the database.
        """
        
        query = f"""
            MATCH (n:object)
            RETURN distinct n.object as object;
            """
        session = self.driver.session()
        result = session.run(query)
        df_result = pd.DataFrame(result)
        result = list(df_result[0])
        result = list(set(result))
        return result

    # 노드 내 모든 object 
    def get_object(self, object = False):
        """
        A function to find the desired object as a node.

        :param object:  The desired objects stored in the database.
        """
        
        # 구문 생성
        # 1. match 구문
        q_match = f"MATCH (n) "
        
        # 2. with 구문
        q_with = f"WITH *"
        
        # 3. where 구문    
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

        if object:
            q_where = f"WHERE "+ q_obj + '\n'
        else:
            q_where = '\n'

        # 4. return 구문
        q_return = f"RETURN n.object as object, n.video_id as video_id, n.object_id as object_id;"

        # 5. 전체 쿼리생성 및 실행
        query = q_match + '\n'+ q_with + '\n'+ q_where + '\n' + q_return
        start_time = time.time()
        
        session = self.driver.session()                    
        result = session.run(query)
        
        end_time = time.time()
        out = result.data()
        df_result = pd.DataFrame(out)   

        print("total time elapsed: ", end_time-start_time)
        return df_result

    def get_predicate_list(self):
        """
        A function that outputs a unique list of predicates stored in the database.
        """
        query = f"""
            CALL db.relationshipTypes()
            """
        session = self.driver.session()
        result = session.run(query)
        df_result = pd.DataFrame(result)
        results = list(df_result[0])        
        return results

    def get_spo(self, video_id = False, subject = False, sp_link = False, object = False, po_link = False, so_link = False, predicate = False):
        """
        A function that extracts SPOs with a specific subject, object, or predicate.

        :param subject:    An argument that extracts spos with a specific subject.
        :param predicate:  An argument that extracts spos with a specific predicate.
        :param object:     An argument that extracts spos with a specific object.

        :param sp_link:    An argument that specifies how to extract specific subjects and predicates. When given the 'or' option, it outputs spos that match either the designated subject or predicate. When given the 'and' option, it outputs spos where both the designated subject and predicate match.
        
        :param po_link:    An argument that specifies how to extract specific predicates and objects. When given the 'or' option, it outputs spos that match either the designated predicates or objects. When given the 'and' option, it outputs spos where both the designated predicates and objects match.
        
        :param so_link:    An argument that specifies how to extract specific subjects and objects. When given the 'or' option, it outputs spos that match either the designated subject or objects. When given the 'and' option, it outputs spos where both the designated subject and objects match.
        """
        print("video_id:")
        video_id_list = input()
        print(video_id_list)
    
        print("subject:")
        subject = input()
        print(subject)
        
        if subject == '':
            subject = False
                        
        print("object:")
        object = input()
        print(object)

        if object == '':
            object = False

        print("predicate:")
        predicate = input()
        print(predicate)

        if predicate == '':
            predicate = False
        
        if subject and object:
            print("How to link subjects and and objects?")
            print("If you use AND, the spo satisfying both subject and object is searched. If you use OR, the spo satisfying either the subject or the object is searched.")
            so_link = input()
            print(so_link)

        if subject and predicate:
            print("How to link subjects and and predicates?")
            print("If you use AND, the spo satisfying both subject and predicates is searched. If you use OR, the spo satisfying either the subject or the predicates is searched.")
            sp_link = input()
            print(sp_link)
            
        if predicate and object:
            print("How to link predicates and and objects?")
            print("If you use AND, the spo satisfying both predicates and objects is searched. If you use OR, the spo satisfying either the predicates or the objects is searched.")
            po_link = input()
            print(po_link)

        ## input 정리
        # if subject_list:
        #     subject_list = subject_list.split(', ')
        #     subject = []
        #     for i, r in enumerate(subject_list):
        #         subject.append(r)
        # else:
        #     subject = False
            
        # if object_list:
        #     object_list = object_list.split(', ')
        #     object = []
        #     for i, r in enumerate(object_list):
        #         object.append(r)
        # else:
        #     object = False
            
        # if predicate_list:
        #     predicate_list = predicate_list.split(', ')
        #     predicate = []
        #     for i, r in enumerate(predicate_list):
        #         predicate.append(r)
        # else:
        #     predicate = False
            
        if video_id_list:
            video_id_list = video_id_list.split(', ')
            video_id = []
            for i, r in enumerate(video_id_list):
                video_id.append(r)
        else:
            video_id = False
        
        ## link 정리
        if subject and predicate:
            if sp_link == False:
                sp_link = ' and '
            else:
                sp_link = sp_link
        elif predicate == False or object == False:
            sp_link = ''

        #
        if predicate and object:
            if po_link == False:
                po_link = ' and '
            else:
                po_link = po_link
        elif object == False or subject == False:
            po_link = ''

        #
        if subject and object:
            if so_link == False:
                so_link = ' and '
            else:
                so_link = so_link
        elif subject == False or predicate == False:
            so_link = ''

        ## 구문 생성
        # 1. match 구문
        match = f"MATCH (s:object)-[r]->(o:object) "
        
        # 2. where 구문
        if subject == False:
            s_where = ' '
        else:
            subj = subject.split(', ')
            for i, sub in enumerate(subj):
                # sub = sub.replace(' ', '')
                if i == 0:
                    s_where = f" (startNode(r).object = '{sub}' "
                else:
                    s_where = s_where + f" or startNode(r).object = '{sub}' "
            s_where = s_where + ") "
            # s_where = f" startNode(r).object IN {subject} "
        
        if object == False:
            o_where = ' '
        else:
            obj = object.split(', ')
            for i, ob in enumerate(obj):
                # sub = sub.replace(' ', '')
                if i == 0:
                    o_where = f" (endNode(r).object = '{ob}' "
                else:
                    o_where = o_where + f" or endNode(r).object = '{ob}' "
            o_where = o_where + ") "            
            # o_where = f" endNode(r).object IN {object} "
            
        if predicate == False:
            p_where = ' '
        else:
            pred = predicate.split(', ')
            for i, prd in enumerate(pred):
                # sub = sub.replace(' ', '')
                if i == 0:
                    p_where = f" (type(r) = '{prd}' "
                else:
                    p_where = p_where + f" or type(r) = '{prd}' "
            p_where = p_where + ") "        
            # p_where = f" type(r) IN {predicate} "
        
        # where video
        if video_id:
            w_video = ""
            for ii, vid in enumerate(video_id):
                if ii == 0:
                    w_video = w_video + f"r.video_id ='{vid}'"
                else:
                    w_video = w_video + f" or r.video_id ='{vid}'"
            w_video = "(" + w_video + ")"

        #
        if subject and object and predicate == False:
            where = "WHERE (" + s_where + so_link + o_where + ")"
        elif so_link == 'and' and po_link == 'or':
            where = "WHERE (" + s_where + so_link + o_where + po_link + p_where + ")"
        else:
            where = "WHERE (" + s_where + sp_link + p_where + po_link + o_where + ")"

        if video_id:
            where = where + " and " + w_video
        else:
            where = where 

        #    
        if subject == False and object == False and predicate == False:
            where = ' '
            if video_id_list:
                where = "where " + w_video 
        
        # 3. with 구문
        with_q = "WITH r.video_id AS video_id, r.video_path AS video_path, r.captions AS captions, properties(r) AS prop_r, type(r) AS predicate, startNode(r) AS startNode, endNode(r) AS endNode, [startNode(r).object, type(r), endNode(r).object] AS spo, [properties(r).begin_frame, properties(r).end_frame] AS frame"
        
        if subject:
            with_s = " COLLECT(DISTINCT startNode.object) as sub_cond "
        else:
            with_s = ''
            
        if object:
            with_o = "COLLECT(DISTINCT endNode.object) as ob_cond"
        else:
            with_o = ''
        
        if predicate:
            with_p = "COLLECT(DISTINCT predicate) as pred_cond "
        else:
            with_p = ''
        
        with_spo = ''
        if subject:
            if predicate == False and object == False:
                with_spo = ', ' + with_s
            if predicate and object == False:
                with_spo = ', ' + with_s + ', ' + with_p
            if predicate == False and object:
                with_spo = ', ' + with_s + ', ' + with_o
            if predicate and object:
                with_spo = ', ' + with_s + ', ' + with_p + ', ' + with_o
        elif subject == False:
            if predicate and object == False:
                with_spo = ', ' + with_p
            elif predicate == False and object:
                with_spo = ', ' + with_o
            elif predicate and object:
                with_spo = ', ' + with_p + ', ' + with_o
        
        with_q = with_q + '\n' + "WITH video_id, video_path, captions, collect(DISTINCT spo) as spo, collect(frame) as frame" + with_spo

        # # 4. where 구문
        # if subject == False:
        #     s_where2 = ' '
        # else:
        #     s_where2 = f" ALL(cd IN {subject} WHERE cd IN sub_cond) "
        
        # if object == False:
        #     o_where2 = ' '
        # else:
        #     o_where2 = f" ALL(cd IN {object} WHERE cd IN ob_cond) "
            
        # if predicate == False:
        #     p_where2 = ' '
        # else:
        #     p_where2 = f" ALL(cd IN {predicate} WHERE cd IN pred_cond) "
        
        # where2 = ''

        # if subject and object and predicate == False:
        #     where2 = "WHERE " + s_where2 + 'or' + o_where2
        # elif subject and object == False and predicate:
        #     where2 = "WHERE " + s_where2 + 'or' + o_where2
        # elif subject == False and object and predicate:
        #     where2 = "WHERE " + p_where2 + 'or' + o_where2
        # elif subject and object and predicate:
        #     where2 = "WHERE "+ s_where2 + 'or' + p_where2 + 'or' + o_where2
            
        # if subject == False and object == False and predicate == False:
        #     where2 = ''
                
        # 5. return 구문
        return_q = "RETURN video_id, video_path, captions, spo, frame"
        
        query = match + '\n' + where + '\n' + with_q + '\n' + return_q
        print(query)
        session = self.driver.session()                    
        result = session.run(query)
        end_time = time.time()
        out = result.data()
        out = pd.DataFrame(out) 
        return out
        