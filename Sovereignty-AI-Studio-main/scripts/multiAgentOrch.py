# agents:
#   - id: backend
#     role: Backend Engineer
#     goal: Propose an API design
# 
#   - id: frontend
#     role: Frontend Engineer
#     goal: Propose a UI layout
# 
#   - id: reviewer
#     role: Tech Lead
#     goal: Review and consolidate proposals
# 
# workflow:
#   type: parallel
#   branches:
#     - backend
#     - frontend
#   then:
#     agent: reviewer