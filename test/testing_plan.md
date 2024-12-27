# Testing Plan

Testing is done using pytest module.

## Current Plan
1. Install the requirements
2. Run the cpu_monitor.py file
3. Check if the CPU monitor window opens and displays correctly
4. Verify that all CPU cores are detected and displayed
5. Check if the "All Cores" checkbox selects all the cores
6. Test changing governors:
  - Change governor for individual cores
  - Use "All Cores" to change governor for all cores at once
  - Verify governors are actually applied
7. Test command line interface:
  - Set governor for specific core
  - Set max frequency
  - Set EPP value
8. Test signal handling:
  - Verify graceful shutdown with Ctrl+C
  - Check cleanup on program exit
9. Error handling:
   - Try invalid governor selections
   - Test with insufficient privileges
   - Verify appropriate error messages


## Future Plan
10. Performance testing:
   - Monitor CPU usage of the application
   - Check update frequency of CPU info
11. UI responsiveness:
   - Verify UI remains responsive while updating
   - Test rapid governor/EPP changes
12. For AMD CPUs with pstate support:
   - Test Energy Performance Preference (EPP) settings
   - Verify AMD params dialog opens and functions
   - Test applying different EPP values