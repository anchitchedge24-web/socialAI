from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app, allowed_origins: list):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )