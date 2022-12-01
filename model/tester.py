import os, traceback, random, threading, shutil, time

import tensorflow as tf
import pandas as pd
import numpy as np

from pathlib import Path
from tqdm import tqdm
from data.data_manager import DataManager
from environment import KGEnv
from agent import Agent
from keras.models import load_model

from config import get_config

# Global GUI values
tst_total_iterations, tst_current_iteration = 0, 0
tst_total_iter_steps, tst_current_iter_steps = 0, 0

def run_prep(TESTS):
    modelpath = Path(__file__).parent.absolute()
    modelpath = modelpath.resolve()

    agents_paths, respaths, dataframes,  = [], [], []

    for t in TESTS:
        respath = Path(f"{modelpath}/data/results/{t.name}").resolve()
        try:
            shutil.rmtree(respath)
            os.mkdir(respath)
        except:
            os.mkdir(respath)
        
        respaths.append(respath)

        a_path = Path(f"{modelpath}/data/agents/{t.agent_name}")
        agents_paths.append(a_path)

        n = len(t.embeddings)

        df_index = [
            np.array([
            *["hits@1"]*n,*["hits@3"]*n,*["hits@5"]*n,*["hits@10"]*n,*["MRR"]*n,
            ]),
            np.array([*t.embeddings]*5)
        ]

        metrics_df = pd.DataFrame(
            columns = [t.dataset],
            index = df_index
        )

        dataframes.append(metrics_df)

    return dataframes, agents_paths, respaths

class Tester(object):
    '''
    Test the model and calculate MRR & Hits@N metrics.
    '''
    def __init__(self, respath, env_config, agent_models, emb, app, alg, rwt, srp):
        for key, val in env_config.items(): setattr(self, key, val)

        if (self.random_seed):
            seed = random.randint(0, (2**32)-1)
        else:
            seed = self.seed

        self.set_gpu_config(self.gpu_acceleration)

        self.update_gui_vars(tot_steps=1, curr_step=0, progtext="Initializing Tester...")
        self.is_ready = False

        self.dm = DataManager(is_experiment=False, experiment_name=self.name, respath=respath)

        self.env = KGEnv(self.dm, self.dataset, srp, emb, False, seed, 8, self.path_length,
         False, False, self.gpu_acceleration, True, 0, False)

        self.agent = Agent(self.dm, self.env, 0.99, 1e-4, True, "leaky_relu", [],"max_percent",
        [], app, alg, True, 0.9, rwt, True, verbose = self.verbose, debug = self.debug)

        if(len(agent_models) == 1):
            self.agent.policy_network = agent_models[0]
        
        elif(len(agent_models) == 2):
            self.agent.policy_network = agent_models[0]
            self.agent.critic = agent_models[1]

    def run(self):
        self.is_ready = True
        MRR = []
        hits_at = {i: 0 for i in (1, 3, 5, 10)}
        found_paths = []
        self.update_gui_vars(tot_steps = self.episodes, progtext="Running Tester...")
        try:
            for x in tqdm(range(self.episodes)):
                self.update_gui_vars(curr_step = x+1)

                MRR.append(0)
                found_tail = False
                for i in range(1, 11):
                    #reset and build path
                    self.env.reset()
                    for _ in range(self.path_length):
                        action = self.agent.select_action_runtime()
                        self.env.step(action)

                    # if tail entity in paths compute hits at.
                    if(self.path_contains_entity()):
                        found_tail = True
                        for n, val in hits_at.items():
                            if i <= n:
                                hits_at[n] = val + 1
                        
                        MRR[x] = i
                        break

                if(found_tail):
                    found_paths.append(self.env.path_history)
            
            self.generate_MRR_boxplot_and_source(MRR)
            self.generate_found_paths_files(found_paths)

            return hits_at, MRR
    
        except Exception as e:
            print(traceback.format_exc())
            return False
    
    def generate_MRR_boxplot_and_source(self, MRR):
        source_filepath = f"{self.dm.test_result_path}/res.txt"
        with open(source_filepath, "w") as f:
            f.write(str(MRR))
        
    def generate_found_paths_files(self, found_paths):
        source_filepath = f"{self.dm.test_result_path}/paths.txt"
        with open(f"{source_filepath}", "w") as f:
            for p in found_paths:
                f.write(f"{p}\n")

    def path_contains_entity(self):
        visited = set()
        path = self.env.path_history 
        entity = self.env.target_triple[2]
        for s in path:
            visited.add(s[2])
        return (entity in visited)
    
    def set_gpu_config(self, use_gpu):
        if not use_gpu:
            try:
                tf.config.set_visible_devices([], 'GPU')
                visible_devices = tf.config.get_visible_devices()
                for device in visible_devices:
                    assert device.device_type != 'GPU'
            except:
                pass

    def update_gui_vars(self, tot_steps = None, curr_step = None, progtext = None):
        if(tot_steps is not None):
            self.total_iter_steps = tot_steps
        
        if(curr_step is not None):
            self.current_iter_steps = curr_step

        if(progtext is not None):
            self.current_progress_text = progtext

# GUI CONNECTOR
class TesterGUIconnector(object):
    def __init__(self, config: dict, tests):
        self.active_tester = None
        self.config, self.tests = config, tests
        self.started = False
        
        global tst_total_iterations
        global tst_current_iteration
        global tst_current_progress_text

        tst_total_iterations = len(tests)
        tst_current_iteration = 1
        tst_current_progress_text = "Intialization"
        
        self.train_thread = threading.Thread(name="testThread", target=self.threaded_update, daemon=True)

    def start_connection(self):
        self.started = True
        self.train_thread.start()

    def update_current_tester(self, t:Tester):
        self.active_tester = t

    def update_info_variables(self):
        global tst_total_iter_steps
        global tst_current_iter_steps
        global tst_current_progress_text

        tst_total_iter_steps = self.active_tester.total_iter_steps
        tst_current_iter_steps = self.active_tester.current_iter_steps
        tst_current_progress_text = self.active_tester.current_progress_text

    def threaded_update(self):
        while(True):
            self.update_info_variables()
            time.sleep(1)

# MISCELLANEOUS

def compute_metrics(mrr, hits, ep):
    hits = [i[1]/ep for i in hits.items()]
    mrr = [1/i if(i != 0) else 0 for i in mrr]
    mrr = sum(mrr)/len(mrr)
    return hits, mrr

def get_agents(agent_path, dataset, embeddings):
    constant_path = f"{agent_path}/{dataset}-"
    agents = dict()

    for e in embeddings:
        ppo = constant_path + e
        base = ppo + ".h5"

        ppo_exist = os.path.isdir(ppo)
        base_exist = os.path.isfile(base)

        if(ppo_exist and base_exist):
            print(f"2 agents found for embedding {e} and dataset {dataset}, remove one.")
        else:
            if(ppo_exist):
                actor = load_model(f"{ppo}/actor.h5")
                critic = load_model(f"{ppo}/critic.h5")
                agents[e] = [actor, critic]

            if(base_exist):
                policy_network = load_model(base)
                agents[e] = [policy_network]

    return agents

def extract_config_info(agent_path):
    with open(f"{agent_path}/config_used.txt") as f:
        for ln in f.readlines():
            if(ln.startswith("action_picking_policy: ")):
                app = ln.lstrip("action_picking_policy: ").rstrip("\n")

            if(ln.startswith("algorithm: ")):
                alg = ln.lstrip("algorithm: ").rstrip("\n")

            if(ln.startswith("reward_type: ")):
                rwt = ln.lstrip("reward_type: ").rstrip("\n")
            
            if(ln.startswith("single_relation_pair: ")):
                aux = ln.lstrip("single_relation_pair: ").rstrip("\n").replace("[","").replace("]","").split(",")
                srp = [aux[0]=="True", None if aux[1].strip()=="None" else aux[1].strip()]

    return app, alg, rwt, srp

################## START ####################
def main(from_file, gui_connector: TesterGUIconnector = None):
    if(from_file):
        config, TESTS = get_config(train=False)
    else:
        print(gui_connector.tests)
        config, TESTS = gui_connector.config, gui_connector.tests

    config ["use_episodes"] = True

    global tst_total_iterations
    global tst_current_iteration

    aux = [len(t.embeddings) for t in TESTS]
    tst_total_iterations = sum(aux)
    tst_current_iteration = 0

    dataframes, agents_paths, respaths = run_prep(TESTS)

    for i, t in enumerate(TESTS):
        agents = get_agents(agents_paths[i], t.dataset, t.embeddings)
        print(f"\nTESTING FOR {t}\n WITH AGENTS: \n{agents}\n")
        app, alg, rwt, srp = extract_config_info(agents_paths[i])

        for emb in t.embeddings:
            tst_current_iteration += 1

            print(f"RUNNING FOR EMBEDDING {emb}\n")
            config["dataset"] = t.dataset
            config["episodes"] = t.episodes
            config["name"] = t.agent_name
            
            sent = agents[emb]
            m = Tester(respaths[i], config, sent, emb, app, alg, rwt, srp)

            if gui_connector is not None:
                gui_connector.update_current_tester(m)
                if(not gui_connector.started):
                    gui_connector.start_connection()

            res = m.run()

            if(res == False):
                print("something went wrong")
                quit()
            
            hits_raw, mrr_raw = res
            hits, mrr = compute_metrics(mrr_raw, hits_raw, config["episodes"])

            dataframes[i].at[("hits@1",emb), t.dataset] = hits[0]
            dataframes[i].at[("hits@3",emb), t.dataset] = hits[1]
            dataframes[i].at[("hits@5",emb), t.dataset] = hits[2]
            dataframes[i].at[("hits@10",emb), t.dataset] = hits[3]
            dataframes[i].at[("MRR",emb), t.dataset] = mrr

            print(dataframes[i])
            dataframes[i].to_csv(f"{respaths[i]}/metrics.csv")

def get_gui_values():
    return tst_total_iterations, tst_current_iteration, tst_total_iter_steps, tst_current_iter_steps, tst_current_progress_text

if __name__ == "__main__":
    main(True)