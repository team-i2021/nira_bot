import asyncio

async def wait(tasks: list) -> None:
    while True:
        tmp = True
        for task in tasks:
            if not task.done():
                tmp = False
                break
        if tmp:
            return
        else:
            await asyncio.sleep(0)
