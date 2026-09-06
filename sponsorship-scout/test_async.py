import asyncio
import threading

async def foo():
    return 1

# emulate what streamlit does: sets a loop on main thread
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = None

if loop is None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# create coro in main thread (which might attach it to main thread's loop implicitly in some python versions, but generally it does so in 3.10+)
coro = foo()

result = []
def _run():
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    result.append(new_loop.run_until_complete(coro))
    new_loop.close()

if loop.is_running():
    t = threading.Thread(target=_run)
    t.start()
    t.join()
else:
    result.append(loop.run_until_complete(coro))

print(result)
