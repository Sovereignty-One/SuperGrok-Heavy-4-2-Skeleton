# agents:
#   - id: reviewer
#     role: Tech Lead
#     goal: Review and consolidate proposals
#     subagents:
#       - id: backend_reviewer
#         role: Backend Reviewer
#         goal: Review backend proposal
#       - id: frontend_reviewer
#         role: Frontend Reviewer
#         goal: Review frontend proposal
# 
# workflow:
#   type: sequential
#   steps:
#     - agent: reviewer