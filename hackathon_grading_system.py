#!/usr/bin/env python3
"""
Hackathon Project Grading System
Evaluates 5 components (PDF, Audio, Video, Codebase, Extra Context) across 4 criteria
with weighted scoring and export functionality.
"""

import json
import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ScoreCell:
    """Represents a single score cell with value and optional comment."""
    value: float
    comment: str = ""

    def __post_init__(self):
        if not 0 <= self.value <= 10:
            raise ValueError(f"Score must be between 0 and 10, got {self.value}")


class HackathonGrader:
    """Main grading system for hackathon projects."""
    
    # Component definitions
    COMPONENTS = ['PDF', 'Audio', 'Video', 'Codebase', 'Extra Context']
    CRITERIA = ['Impact', 'Demo', 'Creativity', 'Pitch']
    
    # Weights for each criterion (must sum to 1.0)
    CRITERION_WEIGHTS = {
        'Impact': 0.25,      # 25% - Long-term potential, alignment with problem statements
        'Demo': 0.50,        # 50% - Implementation quality and functionality
        'Creativity': 0.15,  # 15% - Innovation and uniqueness
        'Pitch': 0.10        # 10% - Presentation effectiveness
    }
    
    def __init__(self):
        """Initialize the grading system."""
        self.scores = {}
        self.project_name = ""
        self.judge_name = ""
        self.grading_date = datetime.now().isoformat()
        
        # Initialize empty score matrix
        self._initialize_matrix()
    
    def _initialize_matrix(self):
        """Initialize empty score matrix."""
        for component in self.COMPONENTS:
            self.scores[component] = {}
            for criterion in self.CRITERIA:
                self.scores[component][criterion] = ScoreCell(0.0)
    
    def get_score(self, component: str, criterion: str) -> ScoreCell:
        """Get score for a specific component and criterion."""
        return self.scores[component][criterion]
    
    def set_score(self, component: str, criterion: str, value: float, comment: str = ""):
        """Set score for a specific component and criterion."""
        self.scores[component][criterion] = ScoreCell(value, comment)
    
    def calculate_component_score(self, component: str) -> float:
        """Calculate weighted score for a specific component."""
        component_scores = self.scores[component]
        total_score = 0.0
        
        for criterion, weight in self.CRITERION_WEIGHTS.items():
            score = component_scores[criterion].value
            total_score += score * weight
        
        return total_score
    
    def calculate_final_score(self) -> float:
        """Calculate final aggregate score across all components."""
        component_scores = []
        for component in self.COMPONENTS:
            component_score = self.calculate_component_score(component)
            component_scores.append(component_score)
        
        return sum(component_scores) / len(component_scores)
    
    def get_score_summary(self) -> Dict:
        """Get comprehensive score summary."""
        component_scores = {}
        for component in self.COMPONENTS:
            component_scores[component] = self.calculate_component_score(component)
        
        return {
            'project_name': self.project_name,
            'judge_name': self.judge_name,
            'grading_date': self.grading_date,
            'component_scores': component_scores,
            'final_score': self.calculate_final_score(),
            'scores': {comp: {crit: asdict(cell) for crit, cell in comp_scores.items()} 
                      for comp, comp_scores in self.scores.items()}
        }
    
    def display_matrix(self):
        """Display the current scoring matrix."""
        print("\n" + "="*80)
        print("HACKATHON PROJECT GRADING MATRIX")
        print("="*80)
        
        # Header
        header = f"{'Component':<20}"
        for criterion in self.CRITERIA:
            header += f"{criterion:<15}"
        header += "Subtotal"
        print(header)
        print("-" * 80)
        
        # Matrix rows
        for component in self.COMPONENTS:
            row = f"{component:<20}"
            for criterion in self.CRITERIA:
                score = self.scores[component][criterion].value
                row += f"{score:<15.1f}"
            
            subtotal = self.calculate_component_score(component)
            row += f"{subtotal:.1f}"
            print(row)
        
        print("-" * 80)
        final_score = self.calculate_final_score()
        print(f"{'FINAL SCORE':<20}{'':<45}{final_score:.1f}/10.0")
        print("="*80)
    
    def get_score_color(self, score: float) -> str:
        """Get color indicator for score ranges."""
        if score >= 8.0:
            return "🟢"  # Green for excellent
        elif score >= 6.0:
            return "🟡"  # Yellow for good
        elif score >= 4.0:
            return "🟠"  # Orange for fair
        else:
            return "🔴"  # Red for poor
    
    def display_detailed_scores(self):
        """Display detailed scores with comments and color coding."""
        print("\n" + "="*80)
        print("DETAILED SCORE BREAKDOWN")
        print("="*80)
        
        for component in self.COMPONENTS:
            print(f"\n📋 {component.upper()}")
            print("-" * 40)
            
            for criterion in self.CRITERIA:
                cell = self.scores[component][criterion]
                color = self.get_score_color(cell.value)
                weight_pct = self.CRITERION_WEIGHTS[criterion] * 100
                
                print(f"{color} {criterion} ({weight_pct:.0f}%): {cell.value:.1f}/10")
                if cell.comment:
                    print(f"   💬 {cell.comment}")
            
            subtotal = self.calculate_component_score(component)
            color = self.get_score_color(subtotal)
            print(f"{color} Component Total: {subtotal:.1f}/10")
        
        final_score = self.calculate_final_score()
        color = self.get_score_color(final_score)
        print(f"\n{color} FINAL PROJECT SCORE: {final_score:.1f}/10.0")
    
    def input_scores(self):
        """Interactive input for all scores."""
        print("\n🎯 HACKATHON PROJECT GRADING")
        print("="*50)
        
        # Get project and judge info
        self.project_name = input("Project Name: ").strip()
        self.judge_name = input("Judge Name: ").strip()
        
        print(f"\n📝 Grading {self.project_name}")
        print("Score each criterion from 0.0 to 10.0")
        print("You can add optional comments for each score")
        
        for component in self.COMPONENTS:
            print(f"\n📋 {component.upper()}")
            print("-" * 30)
            
            for criterion in self.CRITERIA:
                weight_pct = self.CRITERION_WEIGHTS[criterion] * 100
                print(f"\n{criterion} (Weight: {weight_pct:.0f}%)")
                
                while True:
                    try:
                        score_input = input(f"Score (0-10): ").strip()
                        if not score_input:
                            score = 0.0
                        else:
                            score = float(score_input)
                        
                        if 0 <= score <= 10:
                            break
                        else:
                            print("❌ Score must be between 0 and 10")
                    except ValueError:
                        print("❌ Please enter a valid number")
                
                comment = input("Comment (optional): ").strip()
                self.set_score(component, criterion, score, comment)
    
    def save_session(self, filename: str = None):
        """Save current grading session to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self.project_name.replace(" ", "_").replace("/", "_")
            filename = f"grading_session_{safe_name}_{timestamp}.json"
        
        data = self.get_score_summary()
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Grading session saved to: {filename}")
        return filename
    
    def load_session(self, filename: str):
        """Load grading session from JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.project_name = data.get('project_name', '')
            self.judge_name = data.get('judge_name', '')
            self.grading_date = data.get('grading_date', '')
            
            # Load scores
            scores_data = data.get('scores', {})
            for component in self.COMPONENTS:
                if component in scores_data:
                    for criterion in self.CRITERIA:
                        if criterion in scores_data[component]:
                            cell_data = scores_data[component][criterion]
                            self.set_score(component, criterion, 
                                         cell_data['value'], 
                                         cell_data.get('comment', ''))
            
            print(f"✅ Grading session loaded from: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading session: {e}")
            return False
    
    def export_csv(self, filename: str = None):
        """Export scores to CSV format."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self.project_name.replace(" ", "_").replace("/", "_")
            filename = f"grading_results_{safe_name}_{timestamp}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['Hackathon Project Grading Results'])
            writer.writerow(['Project Name', self.project_name])
            writer.writerow(['Judge Name', self.judge_name])
            writer.writerow(['Grading Date', self.grading_date])
            writer.writerow([])
            
            # Matrix header
            header = ['Component'] + self.CRITERIA + ['Subtotal']
            writer.writerow(header)
            
            # Matrix data
            for component in self.COMPONENTS:
                row = [component]
                for criterion in self.CRITERIA:
                    score = self.scores[component][criterion].value
                    row.append(f"{score:.1f}")
                
                subtotal = self.calculate_component_score(component)
                row.append(f"{subtotal:.1f}")
                writer.writerow(row)
            
            # Final score
            writer.writerow([])
            final_score = self.calculate_final_score()
            writer.writerow(['FINAL SCORE', f"{final_score:.1f}/10.0"])
        
        print(f"✅ Results exported to CSV: {filename}")
        return filename
    
    def compare_sessions(self, session_files: List[str]):
        """Compare multiple grading sessions."""
        print("\n" + "="*80)
        print("COMPARISON OF GRADING SESSIONS")
        print("="*80)
        
        sessions = []
        for filename in session_files:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                sessions.append(data)
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")
                continue
        
        if not sessions:
            print("❌ No valid sessions to compare")
            return
        
        # Display comparison table
        print(f"{'Project':<25}{'Judge':<20}{'Final Score':<15}{'Date':<20}")
        print("-" * 80)
        
        for session in sessions:
            project = session.get('project_name', 'Unknown')[:24]
            judge = session.get('judge_name', 'Unknown')[:19]
            score = f"{session.get('final_score', 0):.1f}/10"
            date = session.get('grading_date', '')[:19]
            
            print(f"{project:<25}{judge:<20}{score:<15}{date:<20}")


def main():
    """Main function to run the grading system."""
    grader = HackathonGrader()
    
    while True:
        print("\n" + "="*50)
        print("HACKATHON GRADING SYSTEM")
        print("="*50)
        print("1. Grade New Project")
        print("2. Load Existing Session")
        print("3. Display Current Matrix")
        print("4. Display Detailed Scores")
        print("5. Save Session")
        print("6. Export to CSV")
        print("7. Compare Sessions")
        print("8. Exit")
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == '1':
            grader.input_scores()
            grader.display_matrix()
            
        elif choice == '2':
            filename = input("Enter session filename: ").strip()
            if filename:
                grader.load_session(filename)
                grader.display_matrix()
        
        elif choice == '3':
            if grader.project_name:
                grader.display_matrix()
            else:
                print("❌ No project loaded. Please grade a project first.")
        
        elif choice == '4':
            if grader.project_name:
                grader.display_detailed_scores()
            else:
                print("❌ No project loaded. Please grade a project first.")
        
        elif choice == '5':
            if grader.project_name:
                filename = input("Enter filename (or press Enter for auto): ").strip()
                grader.save_session(filename if filename else None)
            else:
                print("❌ No project to save. Please grade a project first.")
        
        elif choice == '6':
            if grader.project_name:
                filename = input("Enter CSV filename (or press Enter for auto): ").strip()
                grader.export_csv(filename if filename else None)
            else:
                print("❌ No project to export. Please grade a project first.")
        
        elif choice == '7':
            files = []
            while True:
                filename = input("Enter session filename (or 'done'): ").strip()
                if filename.lower() == 'done':
                    break
                if filename:
                    files.append(filename)
            
            if files:
                grader.compare_sessions(files)
        
        elif choice == '8':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-8.")


if __name__ == "__main__":
    main() 