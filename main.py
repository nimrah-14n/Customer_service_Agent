from agents import Runner,Agent,OpenAIChatCompletionsModel,AsyncOpenAI,RunConfig,set_tracing_disabled,function_tool
from openai.types.responses import ResponseTextDeltaEvent
import os
from dotenv import load_dotenv
import chainlit as cl
import requests
load_dotenv()
set_tracing_disabled(disabled=True)
gemini_api_key=os.getenv("GEMINI_API_KEY")

external_client= AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"

)
model=OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)
@function_tool
def track_order(order_id: str) -> str:
    """
    Example tool for tracking orders.
    In real use, connect with database or API.
    """
    if order_id == "123":
        return "📦 Your order #123 has been shipped and will arrive in 2 days."
    elif order_id == "456":
        return "📦 Your order #456 is still being processed. Estimated shipping: 24 hours."
    else:
        return "❌ Sorry, I couldn’t find an order with that ID. Please check and try again."

@function_tool
def refund_policy() -> str:
    """
    Tool for refund policy info.
    """
    return (
        "💰 Codentic Refund Policy:\n\n"
        "- Request a refund within 14 days of purchase.\n"
        "- Product must be unused and in original packaging.\n"
        "- Refunds are processed in 5–7 business days.\n"
        "- For digital products, refunds are valid only if unused.\n\n"
        "Would you like me to guide you through the refund request process?"
    )

config=RunConfig(
    model=model,
    model_provider=external_client,
    # tracing_disabled=True
)
agent=Agent(
    name="Customer service Agent",
    instructions="""You are a helpful customer support assistant for Codentic.
Be professional, kind, and respectful.
Your goal is to answer customer questions politely, clearly, and quickly.
  
"""
)
@cl.on_chat_start
async def handle_start():
    cl.user_session.set("history",[])
    await cl.Message(content="👋 Welcome to Codentic Customer Support! \n\nI'm your AI assistant. How can I help you today?").send()
@cl.on_message
async def handle_message(message:cl.Message):
    history=cl.user_session.get("history")
    history.append({"role":"user","content":message.content})
    msg = cl.Message(content="⏳ Please hold on, I’m checking this for you…")
    await msg.send()

    result=Runner.run_streamed(

        agent,
        input=history,
        run_config=config
    )
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent):
            await msg.stream_token(event.data.delta)
#   msg =cl.Message(content="")
#   await msg.send()
#   async for event in result.stream_events():
#     if event.type=="raw_response_event" and isinstance(event.data,ResponseTextDeltaEvent):
#         await msg.stream_token(event.data.delta)
    history.append({"role":"assistant","content":result.final_output})
    cl.user_session.set("history",history)
    await cl.Message(content=result.final_output).send()

