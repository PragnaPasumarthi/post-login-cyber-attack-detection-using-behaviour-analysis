try:
    from fastapi import FastAPI
    import uvicorn
    import redis
    import sendgrid
    import sklearn
    import pandas
    import numpy
    import joblib
    print("All basic imports successful")
    
    from api.auth import router as auth_router
    from api.actions import router as actions_router
    from api.websocket import router as ws_router
    print("All internal routers imported successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
