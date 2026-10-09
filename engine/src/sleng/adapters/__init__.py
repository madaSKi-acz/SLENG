"""
Purpose:  Ways into the engine from outside Python: HTTP (FastAPI) and the `sleng` command line.
Layer:    sleng.adapters (top layer: may import anything below, nothing imports it)
Exports:  see adapters.http.create_app and adapters.cli.main
Depends:  sleng.container, sleng.config, sleng.domain
Notes:    Adapters only translate: parse input -> call one service -> format output. No logic here.
"""
