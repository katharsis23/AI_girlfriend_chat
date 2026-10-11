

class GfPipeline:
    def __init__(
            self,
            gf_config,
            llm_controller,
            memory_manager,
            expression_manager
    ):
        self.gf_config = gf_config
        self.llm_controller = llm_controller
        self.memory_manager = memory_manager
        self.expression_manager = expression_manager

    async def init():
        ...

    async def chat():
        ...

    async def stream_chat():
        ...

    async def close():
        ...