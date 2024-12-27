import curses
import time
from ..core.cpu_manager import CPUManager

class PopupMenu:
    def __init__(self, stdscr, title, options, start_y=None, start_x=None):
        self.stdscr = stdscr
        self.title = title
        self.options = options
        self.current_selection = 0
        
        # Calculate dimensions and position
        height, width = stdscr.getmaxyx()
        menu_width = max(len(title), max(len(str(i+1) + ". " + opt) for i, opt in enumerate(options))) + 4
        menu_height = len(options) + 4
        
        # Center the popup if no position specified
        self.start_y = start_y if start_y is not None else (height - menu_height) // 2
        self.start_x = start_x if start_x is not None else (width - menu_width) // 2
        
        # Create popup window
        self.window = curses.newwin(menu_height, menu_width, self.start_y, self.start_x)
        self.window.keypad(True)
        
    def show(self):
        while True:
            self.window.box()
            self.window.addstr(1, 2, self.title, curses.A_BOLD)
            
            for i, option in enumerate(self.options):
                if i == self.current_selection:
                    attr = curses.A_REVERSE
                else:
                    attr = curses.A_NORMAL
                self.window.addstr(i + 3, 2, f"{i+1}. {option}", attr)
            
            self.window.refresh()
            
            # Handle input
            key = self.window.getch()
            if key == ord('\n') or key == ord(' '):  # Enter or Space
                return self.options[self.current_selection]
            elif key == 27:  # ESC
                return None
            elif key in [ord(str(i)) for i in range(1, len(self.options) + 1)]:
                return self.options[int(chr(key)) - 1]
            elif key == curses.KEY_UP and self.current_selection > 0:
                self.current_selection -= 1
            elif key == curses.KEY_DOWN and self.current_selection < len(self.options) - 1:
                self.current_selection += 1

class CPUMonitorTUI:
    def __init__(self):
        self.cpu_manager = CPUManager()
        self.selected_cores = set()
        self.current_row = 0
        self.refresh_rate = 1.0
        self.running = True

    def start(self):
        curses.wrapper(self.main)

    def main(self, stdscr):
        # Setup colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        
        # Hide cursor
        curses.curs_set(0)
        
        # Enable keypad input
        stdscr.keypad(True)
        
        # Set nodelay mode for non-blocking getch
        stdscr.nodelay(1)
        
        last_update = 0
        
        while self.running:
            current_time = time.time()
            
            # Handle input
            self.handle_input(stdscr)
            
            # Update display if refresh interval has passed
            if current_time - last_update >= self.refresh_rate:
                try:
                    self.update_display(stdscr)
                    last_update = current_time
                except curses.error:
                    pass
            
            # Small sleep to prevent high CPU usage
            time.sleep(0.1)

    def format_frequency(self, freq):
        """Format frequency in MHz or GHz based on value"""
        try:
            freq_value = float(freq)
            if freq_value >= 1000:
                return f"{freq_value/1000:6.2f} GHz"
            else:
                return f"{freq_value:6.1f} MHz"
        except (ValueError, TypeError):
            return f"{freq:>6} MHz"

    def handle_input(self, stdscr):
        try:
            key = stdscr.getch()
            if key == ord('q'):
                self.running = False
            elif key == ord(' '):  # Space to select/deselect core
                self.selected_cores.symmetric_difference_update([self.current_row])
            elif key == curses.KEY_UP and self.current_row > 0:
                self.current_row -= 1
            elif key == curses.KEY_DOWN and self.current_row < self.cpu_manager.cpu_cores - 1:
                self.current_row += 1
            elif key == ord('a'):  # Select all cores
                if len(self.selected_cores) == self.cpu_manager.cpu_cores:
                    self.selected_cores.clear()
                else:
                    self.selected_cores = set(range(self.cpu_manager.cpu_cores))
            elif key == ord('g'):  # Show governor selection popup
                stdscr.nodelay(0)  # Temporarily disable nodelay for popup
                popup = PopupMenu(stdscr, "Select Governor", self.cpu_manager.available_governors)
                selected = popup.show()
                stdscr.nodelay(1)  # Re-enable nodelay
                if selected:
                    cores_to_update = self.selected_cores or {self.current_row}
                    self.cpu_manager.update_all_governors(selected, cores_to_update)
                stdscr.clear()
                self.update_display(stdscr)
            elif key == ord('e') and self.amd_pstate_active:  # Show EPP selection popup
                info = self.cpu_manager.get_cpu_info(0)
                available_preferences = info.get('energy_performance_available_preferences', '').split()
                if available_preferences:
                    stdscr.nodelay(0)  # Temporarily disable nodelay for popup
                    popup = PopupMenu(stdscr, "Select EPP Profile", available_preferences)
                    selected = popup.show()
                    stdscr.nodelay(1)  # Re-enable nodelay
                    if selected:
                        cores_to_update = self.selected_cores or {self.current_row}
                        self.cpu_manager.update_all_epp(selected, list(cores_to_update))
                    stdscr.clear()
                    self.update_display(stdscr)
        except curses.error:
            pass

    def safe_addstr(self, stdscr, y, x, text, attr=curses.A_NORMAL):
        """Safely add a string to the screen, truncating if necessary."""
        height, width = stdscr.getmaxyx()
        if y < height:
            # Ensure we don't write beyond the screen width
            if x < width:
                # Calculate remaining width
                remaining = width - x
                # Truncate the text if necessary
                if len(text) > remaining:
                    text = text[:remaining]
                try:
                    stdscr.addstr(y, x, text, attr)
                except curses.error:
                    pass

    def update_display(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Display header
        header = "CPU Monitor (TUI) - Press 'q' to quit, 'space' to select, 'a' for all cores"
        self.safe_addstr(stdscr, 0, 0, header, curses.A_BOLD)
        
        # Display available actions
        actions = "Press 'g' for governor selection"
        if self.amd_pstate_active:
            actions += ", 'e' for EPP profile selection"
        self.safe_addstr(stdscr, 1, 0, actions, curses.color_pair(2))
        
        # Display core information with fixed column widths
        for i in range(min(self.cpu_manager.cpu_cores, height - 3)):
            info = self.cpu_manager.get_cpu_info(i)
            
            # Format each column with fixed width
            core_col = f"Core {i:2d}"
            freq_col = f"Freq: {self.format_frequency(info['frequency'])}"
            gov_col = f"Gov: {info['governor']:<12}"
            
            # Build the line with proper spacing
            core_text = f"{core_col:<8} | {freq_col:<20} | {gov_col}"
            
            if self.amd_pstate_active:
                epp_col = f"EPP: {info.get('energy_performance_preference', 'N/A'):<8}"
                core_text += f" | {epp_col}"
            
            # Highlight selected cores
            attrs = curses.color_pair(1) if i in self.selected_cores else curses.A_NORMAL
            # Highlight current row
            if i == self.current_row:
                attrs |= curses.A_REVERSE
            
            self.safe_addstr(stdscr, i + 3, 0, core_text, attrs)
        
        stdscr.refresh()

    @property
    def amd_pstate_active(self):
        return self.cpu_manager.amd_pstate_active 