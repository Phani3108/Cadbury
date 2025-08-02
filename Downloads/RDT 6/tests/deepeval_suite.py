#!/usr/bin/env python3
"""
DeepEval test suite for Digital Twin regression testing.
"""
import os
import sys
import yaml
import asyncio
import requests
from pathlib import Path
from typing import List, Dict, Any
from deepeval import evaluate
from deepeval.metrics import Groundedness, AnswerRelevancy, ContextRelevancy
from deepeval.test_case import LLMTestCase

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class DigitalTwinTestSuite:
    """Test suite for Digital Twin using DeepEval."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_cases = []
        self.load_regression_cases()
    
    def load_regression_cases(self):
        """Load test cases from regression.yaml."""
        yaml_path = Path(__file__).parent / "regression.yaml"
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        for case in data:
            if 'query' in case and 'expect' in case:
                self.test_cases.append({
                    'id': case.get('id', 'unknown'),
                    'query': case['query'],
                    'expect': case['expect']
                })
    
    async def run_query(self, query: str) -> str:
        """Run a query against the Digital Twin API."""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Error: {response.status_code}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def create_test_case(self, case: Dict[str, Any]) -> LLMTestCase:
        """Create a DeepEval test case from regression data."""
        return LLMTestCase(
            input=case['query'],
            actual_output=case.get('response', ''),
            expected_output=case.get('expected', ''),
            context=case.get('context', ''),
            retrieval_context=case.get('retrieval_context', '')
        )
    
    async def run_groundedness_tests(self) -> Dict[str, Any]:
        """Run groundedness tests on all cases."""
        print("🔍 Running Groundedness Tests...")
        
        results = []
        total_score = 0
        
        for case in self.test_cases:
            print(f"Testing: {case['query'][:50]}...")
            
            # Run the query
            response = await self.run_query(case['query'])
            
            # Create test case
            test_case = LLMTestCase(
                input=case['query'],
                actual_output=response,
                context="Digital Twin Knowledge Base"  # Placeholder context
            )
            
            # Evaluate groundedness
            groundedness = Groundedness()
            score = groundedness.measure(test_case)
            
            results.append({
                'id': case['id'],
                'query': case['query'],
                'response': response,
                'groundedness_score': score,
                'passed': score >= 0.9
            })
            
            total_score += score
            print(f"  Groundedness: {score:.3f} {'✅' if score >= 0.9 else '❌'}")
        
        avg_score = total_score / len(results) if results else 0
        passed_count = sum(1 for r in results if r['passed'])
        
        return {
            'total_cases': len(results),
            'passed_cases': passed_count,
            'average_groundedness': avg_score,
            'results': results
        }
    
    async def run_relevancy_tests(self) -> Dict[str, Any]:
        """Run answer and context relevancy tests."""
        print("\n🎯 Running Relevancy Tests...")
        
        answer_relevancy = AnswerRelevancy()
        context_relevancy = ContextRelevancy()
        
        results = []
        
        for case in self.test_cases[:10]:  # Test first 10 cases
            response = await self.run_query(case['query'])
            
            test_case = LLMTestCase(
                input=case['query'],
                actual_output=response,
                context="Digital Twin Knowledge Base"
            )
            
            answer_score = answer_relevancy.measure(test_case)
            context_score = context_relevancy.measure(test_case)
            
            results.append({
                'id': case['id'],
                'query': case['query'],
                'answer_relevancy': answer_score,
                'context_relevancy': context_score,
                'avg_relevancy': (answer_score + context_score) / 2
            })
            
            print(f"  {case['id']}: Answer={answer_score:.3f}, Context={context_score:.3f}")
        
        return {
            'total_cases': len(results),
            'average_answer_relevancy': sum(r['answer_relevancy'] for r in results) / len(results),
            'average_context_relevancy': sum(r['context_relevancy'] for r in results) / len(results),
            'results': results
        }
    
    async def run_full_suite(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        print("🧪 Digital Twin DeepEval Test Suite")
        print("=" * 50)
        
        # Check if server is running
        try:
            health_response = requests.get(f"{self.base_url}/health")
            if health_response.status_code != 200:
                print("❌ Digital Twin server not running")
                return {'error': 'Server not available'}
        except:
            print("❌ Digital Twin server not running")
            return {'error': 'Server not available'}
        
        print("✅ Server is running")
        
        # Run tests
        groundedness_results = await self.run_groundedness_tests()
        relevancy_results = await self.run_relevancy_tests()
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"Total Cases: {groundedness_results['total_cases']}")
        print(f"Passed Groundedness: {groundedness_results['passed_cases']}/{groundedness_results['total_cases']}")
        print(f"Average Groundedness: {groundedness_results['average_groundedness']:.3f}")
        print(f"Average Answer Relevancy: {relevancy_results['average_answer_relevancy']:.3f}")
        print(f"Average Context Relevancy: {relevancy_results['average_context_relevancy']:.3f}")
        
        # Determine overall pass/fail
        groundedness_passed = groundedness_results['average_groundedness'] >= 0.9
        relevancy_passed = (relevancy_results['average_answer_relevancy'] + relevancy_results['average_context_relevancy']) / 2 >= 0.8
        
        overall_passed = groundedness_passed and relevancy_passed
        
        print(f"\n🎯 Overall Result: {'✅ PASSED' if overall_passed else '❌ FAILED'}")
        
        return {
            'overall_passed': overall_passed,
            'groundedness_results': groundedness_results,
            'relevancy_results': relevancy_results
        }

async def main():
    """Run the DeepEval test suite."""
    suite = DigitalTwinTestSuite()
    results = await suite.run_full_suite()
    
    if 'error' in results:
        sys.exit(1)
    
    if not results['overall_passed']:
        sys.exit(1)
    
    print("🎉 All tests passed!")

if __name__ == "__main__":
    asyncio.run(main()) 