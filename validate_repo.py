"""
Validation script for the Code Analyzer Agent.

This script tests the Code Analyzer Agent with a real GitHub repository
(yizucodes/memory) to validate its functionality and analysis capabilities.
"""

import asyncio
import json
import time
import os
from typing import Dict, Any
from dotenv import load_dotenv
from pitchbot.code_analyzer_agent import CodeAnalyzerAgent

# Load environment variables from .env file
load_dotenv()


class ValidationTest:
    """Test suite for validating the Code Analyzer Agent."""
    
    def __init__(self):
        """Initialize the validation test."""
        self.test_repo = "https://github.com/yizucodes/memory"
        self.agent = None
        self.results = {}
        
    async def run_validation(self) -> Dict[str, Any]:
        """Run the complete validation test suite."""
        print("🧪 Code Analyzer Agent Validation Suite")
        print("=" * 60)
        
        # Check prerequisites
        if not self._check_prerequisites():
            return {"error": "Prerequisites not met"}
        
        # Initialize agent
        print("\n🤖 Initializing Code Analyzer Agent...")
        try:
            self.agent = CodeAnalyzerAgent()
            print("✅ Agent initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return {"error": f"Agent initialization failed: {e}"}
        
        # Run analysis
        print(f"\n🔍 Analyzing repository: {self.test_repo}")
        print("This is the yizucodes/memory repository - a Llama-powered personal memory system")
        print("for processing Meta Ray-Ban glasses footage.")
        print("\nAnalysis may take 2-5 minutes depending on repository size...")
        
        start_time = time.time()
        
        try:
            analysis_result = await self.agent.analyze_github_repository(self.test_repo)
            analysis_time = time.time() - start_time
            
            # Validate results
            validation_results = self._validate_analysis_results(analysis_result, analysis_time)
            
            return {
                "status": "success",
                "repository": self.test_repo,
                "analysis_time": f"{analysis_time:.2f} seconds",
                "analysis_result": analysis_result,
                "validation": validation_results
            }
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return {
                "status": "failed",
                "repository": self.test_repo,
                "error": str(e),
                "analysis_time": f"{time.time() - start_time:.2f} seconds"
            }
    
    def _check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        print("\n🔧 Checking prerequisites...")
        
        # Check LLAMA API key
        llama_key = os.getenv('LLAMA_API_KEY')
        if not llama_key:
            print("❌ LLAMA_API_KEY not found in environment")
            print("Please set your LLAMA API key in the .env file")
            return False
        else:
            print("✅ LLAMA API key found")
        
        # Check git availability
        try:
            import subprocess
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            print("✅ Git is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git is not available or not in PATH")
            return False
        
        # Check internet connectivity (basic)
        try:
            import urllib.request
            urllib.request.urlopen('https://github.com', timeout=10)
            print("✅ Internet connectivity confirmed")
        except Exception as e:
            print(f"⚠️  Internet connectivity issue: {e}")
            print("Proceeding anyway - may be a temporary issue")
            # Don't return False, just warn
            pass
        
        return True
    
    def _validate_analysis_results(self, result: Dict[str, Any], analysis_time: float) -> Dict[str, Any]:
        """Validate the analysis results."""
        print(f"\n📊 Analysis completed in {analysis_time:.2f} seconds")
        print("🔍 Validating results...")
        
        validation = {
            "structure_valid": False,
            "content_quality": "unknown",
            "expected_technologies": [],
            "detected_technologies": [],
            "technology_accuracy": 0.0,
            "summary_length": 0,
            "pitfalls_count": 0,
            "improvements_count": 0,
            "overall_score": 0.0
        }
        
        # Check if result has error
        if "error" in result and result["error"]:
            print(f"❌ Analysis returned error: {result['error']}")
            validation["content_quality"] = "error"
            return validation
        
        # Validate structure
        required_fields = ["summary", "stacks", "problem_solved", "pitfalls", "improvements"]
        if all(field in result for field in required_fields):
            validation["structure_valid"] = True
            print("✅ Result structure is valid")
        else:
            missing = [field for field in required_fields if field not in result]
            print(f"❌ Missing fields: {missing}")
            return validation
        
        # Validate content
        validation["summary_length"] = len(result.get("summary", ""))
        validation["pitfalls_count"] = len(result.get("pitfalls", []))
        validation["improvements_count"] = len(result.get("improvements", []))
        
        # Expected technologies for yizucodes/memory repository
        expected_techs = ["python", "llama", "whisper", "opencv", "ai", "ml"]
        detected_techs = [tech.lower() for tech in result.get("stacks", [])]
        validation["detected_technologies"] = result.get("stacks", [])
        validation["expected_technologies"] = expected_techs
        
        # Calculate technology detection accuracy
        matches = sum(1 for tech in expected_techs if any(tech in det.lower() for det in detected_techs))
        validation["technology_accuracy"] = matches / len(expected_techs) if expected_techs else 0.0
        
        # Overall quality assessment
        quality_score = 0
        
        # Summary quality (25 points)
        if validation["summary_length"] > 100:
            quality_score += 25
        elif validation["summary_length"] > 50:
            quality_score += 15
        elif validation["summary_length"] > 0:
            quality_score += 5
        
        # Technology detection (25 points)
        quality_score += validation["technology_accuracy"] * 25
        
        # Pitfalls identification (25 points)
        if validation["pitfalls_count"] > 3:
            quality_score += 25
        elif validation["pitfalls_count"] > 1:
            quality_score += 15
        elif validation["pitfalls_count"] > 0:
            quality_score += 10
        
        # Improvements suggestions (25 points)
        if validation["improvements_count"] > 3:
            quality_score += 25
        elif validation["improvements_count"] > 1:
            quality_score += 15
        elif validation["improvements_count"] > 0:
            quality_score += 10
        
        validation["overall_score"] = quality_score
        
        # Determine content quality
        if quality_score >= 80:
            validation["content_quality"] = "excellent"
        elif quality_score >= 60:
            validation["content_quality"] = "good"
        elif quality_score >= 40:
            validation["content_quality"] = "fair"
        else:
            validation["content_quality"] = "poor"
        
        return validation
    
    def print_detailed_results(self, results: Dict[str, Any]):
        """Print detailed validation results."""
        print("\n" + "=" * 80)
        print("📈 DETAILED VALIDATION RESULTS")
        print("=" * 80)
        
        if results.get("status") == "failed":
            print(f"❌ Validation Status: FAILED")
            print(f"Error: {results.get('error', 'Unknown error')}")
            return
        
        print(f"✅ Validation Status: SUCCESS")
        print(f"🕒 Analysis Time: {results.get('analysis_time', 'Unknown')}")
        
        validation = results.get("validation", {})
        print(f"\n📊 Overall Score: {validation.get('overall_score', 0):.1f}/100")
        print(f"🏆 Content Quality: {validation.get('content_quality', 'unknown').upper()}")
        
        print(f"\n📋 Analysis Results:")
        print(f"  • Summary Length: {validation.get('summary_length', 0)} characters")
        print(f"  • Technologies Detected: {len(validation.get('detected_technologies', []))}")
        print(f"  • Pitfalls Identified: {validation.get('pitfalls_count', 0)}")
        print(f"  • Improvements Suggested: {validation.get('improvements_count', 0)}")
        
        print(f"\n🛠️  Technology Detection:")
        detected = validation.get('detected_technologies', [])
        if detected:
            for tech in detected:
                print(f"  • {tech}")
        else:
            print("  • No technologies detected")
        
        accuracy = validation.get('technology_accuracy', 0) * 100
        print(f"  • Detection Accuracy: {accuracy:.1f}%")
        
        # Show actual analysis results
        analysis = results.get("analysis_result", {})
        if analysis and not analysis.get("error"):
            print(f"\n💡 Repository Analysis:")
            print(f"  • Problem Solved: {analysis.get('problem_solved', 'N/A')[:100]}...")
            
            if analysis.get("pitfalls"):
                print(f"\n⚠️  Top Pitfalls:")
                for i, pitfall in enumerate(analysis.get("pitfalls", [])[:3], 1):
                    print(f"  {i}. {pitfall[:80]}...")
            
            if analysis.get("improvements"):
                print(f"\n🚀 Top Improvements:")
                for i, improvement in enumerate(analysis.get("improvements", [])[:3], 1):
                    print(f"  {i}. {improvement[:80]}...")


async def main():
    """Main validation function."""
    validator = ValidationTest()
    
    print("This script will validate the Code Analyzer Agent by analyzing:")
    print("🎯 Repository: yizucodes/memory")
    print("📝 Description: Llama-powered personal memory system for Meta Ray-Ban glasses")
    print("🔧 Features: Video processing, AI transcription, multimodal analysis")
    
    # Run validation
    results = await validator.run_validation()
    
    # Print results
    validator.print_detailed_results(results)
    
    # Save results to file
    with open("validation_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to: validation_results.json")
    
    return results


if __name__ == "__main__":
    print("🧪 Code Analyzer Agent Validation")
    print("Testing with yizucodes/memory repository...")
    print("-" * 50)
    
    # Check if running in virtual environment
    if not os.getenv('VIRTUAL_ENV') and not os.path.exists('.venv'):
        print("⚠️  Warning: Not running in virtual environment")
        print("Consider activating the virtual environment first:")
        print("source .venv/bin/activate")
    
    try:
        results = asyncio.run(main())
        
        # Exit with appropriate code
        if results.get("status") == "success":
            quality = results.get("validation", {}).get("content_quality", "unknown")
            if quality in ["excellent", "good"]:
                exit(0)  # Success
            else:
                exit(1)  # Partial success
        else:
            exit(2)  # Failure
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n❌ Validation failed with exception: {e}")
        exit(3) 