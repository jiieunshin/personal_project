import pandas as pd
import os
import re
import time
from neo4j import GraphDatabase
from tabulate import tabulate
from IPython.display import YouTubeVideo
from gensim.models import KeyedVectors

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
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(self.user, self.password))
        
        q = "CALL dbms.components() YIELD name, versions"
        session = self.driver.session()
        result = session.run(q)
        
        print("-- Successfully connected! --")
        print("connection user name :", self.user)
        print("current neo4j version ", result.data()[0]['versions'][0])
        
        
    def close(self):
        self.neo.close()

    ###############
    ## 2. create ##
    ###############
    def add(self, file):
        """
        Upload a objects to Neo4j"
        
        :param file: data file to load
        """
        
        # create index
        try:
            q = "CREATE INDEX ON :object(video_id);"
            session = self.driver.session()                    
            result = session.run(q)
            # print("index ok")
            
        except Exception as e:
            pass  # 오류를 무시

        # create the objects
        old_q = "MATCH(n) RETURN count(n)"
        session = self.driver.session()                    
        old_count = session.run(old_q)
        
        if old_count:
            old_count = old_count.data()[0]['count(n)']
        else:
            old_count = 0

        q = f"""
            LOAD CSV WITH HEADERS FROM 'file:///{file}' AS row
            WITH row
            WHERE NOT (row.subject IS NULL OR row.video_id IS NULL)
            MERGE (o1:object {{video_id: row.video_id, object: row.subject}})
            ON CREATE SET o1.video_id = row.video_id, o1.object = row.subject

            WITH row
            WHERE NOT (row.object IS NULL OR row.video_id IS NULL)
            MERGE (o2:object {{video_id: row.video_id, object: row.object}})
            ON CREATE SET o2.video_id = row.video_id, o2.object = row.object
            """
        start_time_node = time.time()    
        session = self.driver.session()                    
        node_res = session.run(q)
        end_time_node = time.time()
        time_node = end_time_node - start_time_node
        # print("node ok")

        # create the spos
        q = f"""
            CALL apoc.load.csv('{file}') YIELD lineNo, map AS row
            WITH row WHERE NOT (row.subject IS NULL OR row.predicate IS NULL OR row.object IS NULL)
            CALL {{
            WITH row
            MERGE (s:object {{video_id: row.video_id, object: row.subject}})
            MERGE (o:object {{video_id: row.video_id, object: row.object}})
            WITH s, o, row.predicate AS edgeLabel, row
            WHERE NOT (row.predicate IS NULL OR trim(row.predicate) = '')
            CALL {{
                WITH s, o, edgeLabel, row
                CALL apoc.create.relationship(s, edgeLabel, {{}}, o) YIELD rel
                SET rel += {{
                video_id: row.video_id,
                video_path: row.video_path,
                captions: row.captions,
                begin_frame: row.begin_frame,
                end_frame: row.end_frame,
                subject: row.subject,
                predicate: row.predicate,
                object: row.object
                }}
                RETURN COUNT(rel) AS processedRows, type(rel) AS relType
            }}
            RETURN SUM(processedRows) AS totalProcessedRows, collect(DISTINCT relType) AS uniqueRelTypes
            }}
            WITH sum(totalProcessedRows) AS sum_totalProcessedRows, uniqueRelTypes
            RETURN sum(sum_totalProcessedRows) as n_spo, count(uniqueRelTypes) as n_type
            """
        
        start_time_edge= time.time()
        session = self.driver.session()                    
        rel_res = session.run(q)
        end_time_edge = time.time()
        # print("rel ok")
        time_edge = end_time_edge - start_time_edge

        # extract n_spo and n_type
        result = rel_res.data()[0] 
        n_spo = result['n_spo']
        n_type = result['n_type']

        # finally,
        new_q = "MATCH(n) RETURN count(n)"
        session = self.driver.session()                    
        new_count = session.run(new_q)
        load_count = new_count.data()[0]['count(n)'] - old_count

        print(f"Load the {load_count} objects successfully.")
        print(f"Load the {n_type} relationships and {n_spo} spos successfully.")
        print( )
        print("total time elapsed: ", time_node + time_edge)
        print( )
        print("--please wait for generating page rank--")
        
        ########################
        ## generate page rank ##
        ########################
        # generate comtomizing weight
        query = """
            MATCH (a)-[]->(b)<-[]-(c)
            WHERE id(a) > id(c)
            WITH a, b, c, count(*) as weight
            MERGE (a)-[r:Inter]->(c)
            ON CREATE SET r.w = weight
            """
    
        session = self.driver.session()                    
        result = session.run(query)
    
        # generate temp graph
        query = "CALL gds.graph.create('Graph_Inter', 'object', 'Inter', {relationshipProperties: 'w'})"
        session = self.driver.session()                    
        session.run(query)
        # print("make inter")/
        # generate pageRank
        query = """
            CALL gds.pageRank.write('Graph_Inter', 
            {maxIterations: 20, dampingFactor: 0.85, relationshipWeightProperty: 'w', writeProperty: 'pagerank'})
            YIELD nodePropertiesWritten, ranIterations
            """
        session = self.driver.session()                    
        session.run(query)
        # print("make pagerank")
        
        # remove temp graph
        query = "CALL gds.graph.drop('Graph_Inter');"
        session = self.driver.session()                    
        session.run(query)
    
        # remove temp relation
        query = "MATCH p=()-[r:Inter]->() detach delete r;"
        session = self.driver.session()                    
        session.run(query)
        
 
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
        result1 = session.run(query)
        result1 = result1.data()
    
        query = f"""
            MATCH ()-->() RETURN count(*) as relationship_count; 
            """
        session = self.driver.session()
        result2 = session.run(query)
        result2 = result2.data()
        out1 = [dict(d1, **d2) for d1, d2 in zip(result1, result2)]
        
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
        out2 = result.data()
        
        # result
        print('----node and relation count----')
        print(tabulate(out1, headers='keys', tablefmt='psql', showindex=False))
        print('\n')
        print('----Information for property and relationship----')
        print(tabulate(out2, headers='keys', tablefmt='psql', showindex=False))
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
        q_return = f"RETURN n.object as object, n.video_id as video_id;"

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

    def get_spo(self, video_id = False, subject = False, sp_link = False, object = False, po_link = False, so_link = False, predicate = False, w2v_file = 'activity_w2v'):
        """
        A function that extracts SPOs with a specific subject, object, or predicate.

        :param subject:    An argument that extracts spos with a specific subject.
        :param predicate:  An argument that extracts spos with a specific predicate.
        :param object:     An argument that extracts spos with a specific object.

        :param sp_link:    An argument that specifies how to extract specific subjects and predicates. When given the 'or' option, it outputs spos that match either the designated subject or predicate. When given the 'and' option, it outputs spos where both the designated subject and predicate match.
        
        :param po_link:    An argument that specifies how to extract specific predicates and objects. When given the 'or' option, it outputs spos that match either the designated predicates or objects. When given the 'and' option, it outputs spos where both the designated predicates and objects match.
        
        :param so_link:    An argument that specifies how to extract specific subjects and objects. When given the 'or' option, it outputs spos that match either the designated subject or objects. When given the 'and' option, it outputs spos where both the designated subject and objects match.
        """
        
        ######################
        ## get spo function ##
        ######################
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

        # input 정리
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
            
        if video_id_list:
            video_id_list = video_id_list.split(', ')
            video_id = []
            for i, r in enumerate(video_id_list):
                video_id.append(r)
        else:
            video_id = False
        
        ## link 정리
        if subject and predicate:
            if not sp_link:
                sp_link = ' and '
            else:
                sp_link = sp_link
        elif not predicate or not object:
            sp_link = ''
        elif not subject:
            sp_link = ''

        #
        if predicate and object:
            if not po_link:
                po_link = ' and '
            else:
                po_link = po_link
        elif not object or not subject:
            po_link = ''

        #
        if subject and object:
            if not so_link:
                so_link = ' and '
            else:
                so_link = so_link
        elif not subject or not predicate:
            so_link = ''

        ## 구문 생성  
        # 1. match 구문
        match = f"MATCH (s:object)-[r]->(o:object) "
        
        # 2. where 구문
        if not subject:
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
        
        if not object:
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
            
        if not predicate:
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
        if subject and object and not predicate:
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
        if not subject and not object and not predicate:
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
            if not predicate and not object:
                with_spo = ', ' + with_s
            if predicate and not object:
                with_spo = ', ' + with_s + ', ' + with_p
            if not predicate and object:
                with_spo = ', ' + with_s + ', ' + with_o
            if predicate and object:
                with_spo = ', ' + with_s + ', ' + with_p + ', ' + with_o
        elif not subject:
            if predicate and not object:
                with_spo = ', ' + with_p
            elif not predicate and object:
                with_spo = ', ' + with_o
            elif predicate and object:
                with_spo = ', ' + with_p + ', ' + with_o
        
        with_q = with_q + '\n' + "WITH video_id, video_path, captions, collect(DISTINCT spo) as spo, collect(frame) as frame" + with_spo
                
        # 5. return 구문
        return_q = "RETURN video_id, video_path, captions, spo, frame"
        
        query = match + '\n' + where + '\n' + with_q + '\n' + return_q
        # print(query)
        session = self.driver.session()
        start_time = time.time()
        result = session.run(query)
        end_time = time.time()
        print("total time elapsed: ", end_time-start_time)
        
        out = result.data()
        out = pd.DataFrame(out)

        print(tabulate(out, headers='keys', tablefmt='psql', showindex=False))
        print(f"Total number of retrieves : {len(out)}")
        
        ###########
        ## video ##
        ###########
        if len(out) !=0:            
            video = self.embed_video(out["video_path"][0])
        else:
            video = "No appropriate scene found."
            
        ###############
        ## expansion ##
        ###############
        exp_start_time = time.time()   
        if len(out) == 0:
            subj_w2v = ''
            obj_w2v = ''
            pred_w2v = ''
            
            if subject == False:
                s_where = ' '
            else:
                subj = subject.split(', ')
                subj_w2v = self.w2v(subj, w2v_file)
                for i, sub in enumerate(subj_w2v):
                    if i == 0:
                        s_where = f" (startNode(r).object = '{sub}' "
                    else:
                        s_where = s_where + f" or startNode(r).object = '{sub}' "
                s_where = s_where + ") "
                
            if object == False:
                o_where = ' '
            else:
                obj = object.split(', ')
                obj_w2v = self.w2v(obj, w2v_file)
                for i, ob in enumerate(obj_w2v):
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
                pred_w2v = self.w2v(pred, w2v_file)
                for i, prd in enumerate(pred_w2v):
                    if i == 0:
                        p_where = f" (type(r) = '{prd}' "
                    else:
                        p_where = p_where + f" or type(r) = '{prd}' "
                p_where = p_where + ") "
        
            #
            if subject and object and predicate == False:
                where = "WHERE (" + s_where + so_link + o_where + ")"
            elif so_link == 'and' and po_link == 'or':
                where = "WHERE (" + s_where + so_link + o_where + po_link + p_where + ")"
            else:
                where = "WHERE (" + s_where + sp_link + p_where + po_link + o_where + ")"
        
            #    
            if subject == False and object == False and predicate == False:
                where = ' '

            query = match + '\n' + where + '\n' + with_q + '\n' + return_q
            # print(query)
            session = self.driver.session()      
            result = session.run(query)
            exp_end_time = time.time()
            out = result.data()
            print("total time elapsed for expansion: ", exp_end_time-exp_start_time)
            out = pd.DataFrame(out) 
            print("")
            print("There are no scenes searched by the keyword you entered.")
            print("We will proceed with the search including similar words.")
            if subj_w2v:
                print("Subject - Search & Extension Keywords : {}".format(subj_w2v))
            if obj_w2v:
                print("Object - Search & Extension Keywords : {}".format(obj_w2v))
            if pred_w2v:
                print("Predicate - Search & Extension Keywords : {}".format(pred_w2v))
            print("")
            print(tabulate(out, headers='keys', tablefmt='psql', showindex=False))
            
            print(f"Total number of retrieves for expansion : {len(out)}")
            
            # video
            if len(out) !=0:            
                video = self.embed_video(out["video_path"][0])   
            else:
                video = "No appropriate scene found."
        
        return video
        # return out

    def w2v(self, query, w2v_file):
        n = 1
        result = []
        model = KeyedVectors.load_word2vec_format(os.getcwd() + '\\' + w2v_file)
            
        for word in query:
            similar = []
            result.append(word)
            similar.append(model.most_similar(word))
            for j in similar:
                for num in range(n):
                    result.append(j[num][0])
        return list(set(result))
        
    def embed_video(self, url):
        embed_url = url
        embed_id = embed_url[32:]
        video = YouTube(embed_id, width=400)
        return video            