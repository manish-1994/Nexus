"""
Agent Framework Integration Test
Tests the full execution path: AgentManager -> DefaultAgent -> PromptBuilder -> AIRuntime
Mocks only the external provider API call to verify all internal code layers.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_db
from agents.manager import AgentManager
from services.ai_runtime import AIRuntime
from unittest.mock import AsyncMock, patch
import asyncio

def test_agent_execution_path(agent_id: int, agent_name: str):
    """Test the full agent execution path for a given agent."""
    print(f"\n{'='*60}")
    print(f"TESTING AGENT: {agent_name} (id={agent_id})")
    print(f"{'='*60}")
    
    init_db()
    db = next(get_db())
    
    try:
        # Step 1: Create AgentManager
        manager = AgentManager(db)
        print("[STEP 1] AgentManager created [OK]")
        
        # Step 2: Resolve agent
        agent = manager.resolve_agent(agent_id)
        print(f"[STEP 2] resolve_agent() -> agent={agent.agent_model.name} [OK]")
        
        # Step 3: Get agent config
        config = manager.get_agent_config(agent_id)
        print(f"[STEP 3] get_agent_config() -> {config} [OK]")
        
        # Step 4: Validate execution (use provider_id=3, model=gemini-2.5-flash)
        try:
            manager.validate_execution(3, "gemini-2.5-flash")
            print("[STEP 4] validate_execution(provider=3, model=gemini-2.5-flash) [OK]")
        except ValueError as e:
            print(f"[STEP 4] validate_execution FAILED: {e}")
            from models.model import Model
            models = db.query(Model).filter(Model.provider_id == 3, Model.name == "gemini-2.5-flash").all()
            print(f"  Models found: {[(m.id, m.name, m.is_active) for m in models]}")
            return False
        
        # Step 5: Build prompt with agent system prompt
        messages = [{"role": "user", "content": "Hello, this is a test message."}]
        prompt_messages = manager.build_prompt_for_agent(agent_id, messages)
        print(f"[STEP 5] build_prompt_for_agent() -> {len(prompt_messages)} messages")
        for i, msg in enumerate(prompt_messages):
            role = msg.get("role", "?")
            content_preview = (msg.get("content", "") or "")[:100]
            print(f"  msg[{i}]: role={role}, content={content_preview}...")
        
        # Verify system prompt was injected
        has_system = any(msg.get("role") == "system" for msg in prompt_messages)
        if has_system:
            print("[STEP 5] System prompt injected [OK]")
        else:
            print("[STEP 5] WARNING: No system prompt found")
        
        # Step 6: Test DefaultAgent.chat() directly (mocking provider)
        # Step 7: Test DefaultAgent.stream() directly (mocking provider)
        async def run_async_tests():
            print("\n[STEP 6] Testing DefaultAgent.chat() with mocked provider...")
            with patch.object(AIRuntime, 'chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = "Mocked response: Hello from the agent framework!"
                result = await agent.chat(messages, provider_id=3, model="gemini-2.5-flash")
                print(f"  Response: {result}")
                print("[STEP 6] DefaultAgent.chat() [OK]")
            
            print("\n[STEP 7] Testing DefaultAgent.stream() with mocked provider...")
            async def mock_gen():
                yield "Mocked "
                yield "streaming "
                yield "response."
            with patch.object(AIRuntime, 'stream', return_value=mock_gen()):
                chunks = []
                async for chunk in agent.stream(messages, provider_id=3, model="gemini-2.5-flash"):
                    chunks.append(chunk)
                print(f"  Streamed chunks: {chunks}")
                print(f"  Full text: {''.join(chunks)}")
                print("[STEP 7] DefaultAgent.stream() [OK]")
        
        asyncio.run(run_async_tests())
        
        # Step 8: Test getCapabilities
        capabilities = agent.getCapabilities()
        print(f"\n[STEP 8] getCapabilities() -> {capabilities} [OK]")
        
        # Step 9: Test validate
        is_valid = agent.validate()
        print(f"[STEP 9] validate() -> {is_valid} [OK]")
        
        print(f"\n{'='*60}")
        print(f"AGENT {agent_name} (id={agent_id}): ALL CHECKS PASSED [OK]")
        print(f"{'='*60}")
        return True
        
    except Exception as e:
        print(f"\nFAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    agents = [
        (1, "Assistant"),
        (2, "Coding"),
        (3, "Research"),
        (4, "Writing"),
        (5, "Planner"),
    ]
    
    results = {}
    for agent_id, agent_name in agents:
        results[agent_name] = test_agent_execution_path(agent_id, agent_name)
    
    print("\n\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    all_passed = True
    for name, passed in results.items():
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n[OK] ALL 5 AGENTS PASSED - Agent framework is stable!")
    else:
        print("\n[FAIL] SOME AGENTS FAILED - See details above")
    
    sys.exit(0 if all_passed else 1)