#!/usr/bin/env python3
"""
Quick test script to verify get_allocation_overview() implementation.
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.reports.service import get_allocation_overview

def test_allocation_overview():
    """Test the get_allocation_overview function."""
    print("Testing get_allocation_overview()...")
    
    try:
        result = get_allocation_overview()
        
        print("\n✓ Function executed successfully!")
        print(f"\nResults:")
        print(f"  Total Faculty: {result['total_faculty']}")
        print(f"  Overloaded: {result['overloaded_count']}")
        print(f"  Balanced: {result['balanced_count']}")
        print(f"  Underloaded: {result['underloaded_count']}")
        print(f"  Records: {len(result['records'])}")
        
        # Show a sample record if available
        if result['records']:
            sample = result['records'][0]
            print(f"\nSample Record:")
            print(f"  Employee Code: {sample['emp_code']}")
            print(f"  Name: {sample['name']}")
            print(f"  Total TCH: {sample['total_tch']}")
            print(f"  Workload Status: {sample['workload_status']}")
            print(f"  Assigned Subjects: {sample['assigned_subjects_count']}")
            
            if sample['assigned_subjects']:
                print(f"\n  First Assigned Subject:")
                subj = sample['assigned_subjects'][0]
                print(f"    Code: {subj['subject_code']}")
                print(f"    Name: {subj['subject_name']}")
                print(f"    TCH: {subj['tch']}")
        
        # Verify data structure
        assert 'total_faculty' in result
        assert 'overloaded_count' in result
        assert 'balanced_count' in result
        assert 'underloaded_count' in result
        assert 'records' in result
        assert isinstance(result['records'], list)
        
        # Verify record structure if records exist
        if result['records']:
            rec = result['records'][0]
            assert 'staff_id' in rec
            assert 'emp_code' in rec
            assert 'name' in rec
            assert 'total_tch' in rec
            assert 'assigned_subjects_count' in rec
            assert 'workload_status' in rec
            assert 'assigned_subjects' in rec
            assert isinstance(rec['assigned_subjects'], list)
            
            # Verify workload status is valid
            assert rec['workload_status'] in ['Overloaded', 'Balanced', 'Underloaded']
            
            # Verify subject structure if subjects exist
            if rec['assigned_subjects']:
                subj = rec['assigned_subjects'][0]
                assert 'subject_code' in subj
                assert 'subject_name' in subj
                assert 'program' in subj
                assert 'semester' in subj
                assert 'section' in subj
                assert 'tch' in subj
        
        print("\n✓ All assertions passed!")
        print("\n✓ Implementation is correct!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_allocation_overview()
    sys.exit(0 if success else 1)
