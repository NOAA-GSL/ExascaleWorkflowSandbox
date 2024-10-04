from chiltepin.rocoto import Workflow

w = Workflow("FV3LAM_wflow.xml")

#print(w)

w.dump("FV3LAM_wflow_test.xml")

#with open("FV3LAM_wflow_test2.xml", "w") as f:
#    w.dump(f)

#w.parse()
#
#print(w.cycledefs)
#print(w.tasks)
