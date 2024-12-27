import curses
import time
from ..core.cpu_manager import CPUManager

class Colors:
    """Color scheme management"""
    # Color indices
    WHITE = 10
    RED = 11
    GREEN = 12
    BLUE = 13
    YELLOW = 14
    MAGENTA = 15
    CYAN = 16
    GRAY = 17
    ORANGE = 18
    
    # Color pair indices
    NORMAL = 1
    SELECTED = 2
    HEADER = 3
    INFO = 4
    BORDER = 5
    FREQUENCY = 6
    GOVERNOR = 7
    EPP = 8
    POPUP_NORMAL = 9
    POPUP_SELECTED = 10
    POPUP_BORDER = 11
    CORE_NUMBER = 12
    
    @staticmethod
    def initialize():
        curses.start_color()
        # Always use the basic colors first to ensure compatibility
        curses.init_pair(Colors.NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(Colors.SELECTED, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(Colors.HEADER, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(Colors.INFO, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(Colors.BORDER, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(Colors.FREQUENCY, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(Colors.GOVERNOR, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(Colors.EPP, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(Colors.POPUP_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(Colors.POPUP_SELECTED, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(Colors.POPUP_BORDER, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(Colors.CORE_NUMBER, curses.COLOR_WHITE, curses.COLOR_BLACK)
        
        # Try to enhance colors if supported
        if curses.can_change_color():
            try:
                curses.init_color(Colors.WHITE, 1000, 1000, 1000)    # Pure white
                curses.init_color(Colors.RED, 1000, 400, 400)        # Bright red
                curses.init_color(Colors.GREEN, 400, 1000, 400)      # Bright green
                curses.init_color(Colors.YELLOW, 1000, 1000, 400)    # Bright yellow
                curses.init_color(Colors.MAGENTA, 1000, 400, 1000)   # Bright magenta
                curses.init_color(Colors.CYAN, 400, 1000, 1000)      # Bright cyan
                curses.init_color(Colors.GRAY, 600, 600, 600)        # Medium gray
                curses.init_color(Colors.ORANGE, 1000, 647, 0)       # Bright orange
                
                # Redefine color pairs with custom colors
                curses.init_pair(Colors.NORMAL, Colors.WHITE, curses.COLOR_BLACK)
                curses.init_pair(Colors.SELECTED, Colors.GREEN, curses.COLOR_BLACK)
                curses.init_pair(Colors.HEADER, Colors.YELLOW, curses.COLOR_BLACK)
                curses.init_pair(Colors.INFO, Colors.CYAN, curses.COLOR_BLACK)
                curses.init_pair(Colors.BORDER, Colors.BLUE, curses.COLOR_BLACK)
                curses.init_pair(Colors.FREQUENCY, Colors.MAGENTA, curses.COLOR_BLACK)
                curses.init_pair(Colors.GOVERNOR, Colors.ORANGE, curses.COLOR_BLACK)
                curses.init_pair(Colors.EPP, Colors.CYAN, curses.COLOR_BLACK)
                curses.init_pair(Colors.POPUP_NORMAL, Colors.WHITE, Colors.GRAY)
                curses.init_pair(Colors.POPUP_SELECTED, Colors.YELLOW, Colors.BLUE)
                curses.init_pair(Colors.POPUP_BORDER, Colors.BLUE, curses.COLOR_BLACK)
                curses.init_pair(Colors.CORE_NUMBER, Colors.GREEN, curses.COLOR_BLACK)
            except curses.error:
                pass  # Fallback to basic colors if any error occurs

class BaseWindow:
    def __init__(self, stdscr, title, height, width, start_y=None, start_x=None):
        self.stdscr = stdscr
        self.title = title
        
        # Calculate position
        screen_height, screen_width = stdscr.getmaxyx()
        self.start_y = start_y if start_y is not None else (screen_height - height) // 2
        self.start_x = start_x if start_x is not None else (screen_width - width) // 2
        
        # Create window
        self.window = curses.newwin(height, width, self.start_y, self.start_x)
        self.window.keypad(True)
        self.window.bkgd(' ', curses.color_pair(Colors.POPUP_NORMAL))

class PopupMenu(BaseWindow):
    def __init__(self, stdscr, title, options, start_y=None, start_x=None):
        self.options = options
        self.current_selection = 0
        
        # Calculate dimensions
        menu_width = max(len(title), max(len(str(i+1) + ". " + opt) for i, opt in enumerate(options))) + 4
        menu_height = len(options) + 4
        
        super().__init__(stdscr, title, menu_height, menu_width, start_y, start_x)
        
    def show(self):
        while True:
            try:
                self.window.clear()
                self.window.box()
                
                # Draw title
                self.window.addstr(1, 2, self.title, curses.A_BOLD | curses.color_pair(Colors.HEADER))
                
                # Draw options
                for i, option in enumerate(self.options):
                    if i == self.current_selection:
                        attr = curses.color_pair(Colors.POPUP_SELECTED)
                    else:
                        attr = curses.color_pair(Colors.POPUP_NORMAL)
                    self.window.addstr(i + 3, 2, f"{i+1}. {option}", attr)
                
                self.window.refresh()
                
                # Handle input
                key = self.window.getch()
                if key == ord('\n') or key == ord(' '):
                    return self.options[self.current_selection]
                elif key == 27:  # ESC
                    return None
                elif key in [ord(str(i)) for i in range(1, len(self.options) + 1)]:
                    return self.options[int(chr(key)) - 1]
                elif key == curses.KEY_UP and self.current_selection > 0:
                    self.current_selection -= 1
                elif key == curses.KEY_DOWN and self.current_selection < len(self.options) - 1:
                    self.current_selection += 1
            except curses.error:
                continue  # Try again if there's a display error

class NumberInput(BaseWindow):
    def __init__(self, stdscr, title, max_value):
        self.max_value = max_value
        self.current_value = ""
        
        # Calculate dimensions
        width = max(len(title), len(f"Enter number (0-{max_value}): ") + len(str(max_value))) + 4
        height = 5  # Title + input line + border
        
        super().__init__(stdscr, title, height, width)
        
    def show(self):
        while True:
            try:
                self.window.clear()
                self.window.box()
                
                # Draw title
                self.window.addstr(1, 2, self.title, curses.A_BOLD | curses.color_pair(Colors.HEADER))
                
                # Show current input
                display_text = f"Enter number (0-{self.max_value}): {self.current_value}"
                self.window.addstr(2, 2, display_text, curses.color_pair(Colors.POPUP_NORMAL))
                
                # Show cursor position
                cursor_x = len(display_text) - len(self.current_value) + 2
                self.window.addstr(2, cursor_x + len(self.current_value), " ", curses.A_REVERSE)
                
                self.window.refresh()
                
                # Handle input
                key = self.window.getch()
                if key == ord('\n'):
                    try:
                        value = int(self.current_value) if self.current_value else -1
                        if 0 <= value <= self.max_value:
                            return value
                    except ValueError:
                        pass
                elif key == 27:  # ESC
                    return None
                elif key in [ord(str(i)) for i in range(10)]:
                    if len(self.current_value) < len(str(self.max_value)):
                        self.current_value += chr(key)
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    self.current_value = self.current_value[:-1]
            except curses.error:
                continue  # Try again if there's a display error

class RefreshRateInput(BaseWindow):
    def __init__(self, stdscr, current_rate):
        self.current_value = str(current_rate)
        
        # Calculate dimensions
        title = "Adjust Refresh Rate"
        width = max(len(title), len("Enter refresh rate (seconds): ") + 10) + 4
        height = 6  # Title + input line + info + border
        
        super().__init__(stdscr, title, height, width)
        
    def show(self):
        while True:
            try:
                self.window.clear()
                self.window.box()
                
                # Draw title
                self.window.addstr(1, 2, self.title, curses.A_BOLD | curses.color_pair(Colors.HEADER))
                
                # Show current input
                display_text = f"Enter refresh rate (seconds): {self.current_value}"
                self.window.addstr(2, 2, display_text, curses.color_pair(Colors.POPUP_NORMAL))
                
                # Show info
                info_text = "Press Enter to confirm, ESC to cancel"
                self.window.addstr(3, 2, info_text, curses.color_pair(Colors.INFO))
                
                # Show cursor position
                cursor_x = len(display_text) - len(self.current_value) + 2
                self.window.addstr(2, cursor_x + len(self.current_value), " ", curses.A_REVERSE)
                
                self.window.refresh()
                
                # Handle input
                key = self.window.getch()
                if key == ord('\n'):
                    try:
                        value = float(self.current_value) if self.current_value else 0
                        if value > 0:  # Must be positive
                            return value
                    except ValueError:
                        pass
                elif key == 27:  # ESC
                    return None
                elif key in [ord(str(i)) for i in range(10)] or key == ord('.'):
                    # Allow only one decimal point
                    if key == ord('.') and '.' in self.current_value:
                        continue
                    if len(self.current_value) < 10:  # Limit length
                        self.current_value += chr(key)
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    self.current_value = self.current_value[:-1]
            except curses.error:
                continue  # Try again if there's a display error

class CPUMonitorTUI:
    def __init__(self):
        self.cpu_manager = CPUManager()
        self.selected_cores = set()
        self.current_row = 0
        self.scroll_position = 0
        self.refresh_rate = 1.0
        self.running = True
        self.color_mode = True  # True for colored, False for black & white

    def set_colors(self, stdscr):
        curses.start_color()
        if self.color_mode:
            # Colored mode
            curses.init_pair(Colors.NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.SELECTED, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(Colors.HEADER, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(Colors.INFO, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(Colors.BORDER, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.FREQUENCY, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Restored magenta
            curses.init_pair(Colors.GOVERNOR, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(Colors.EPP, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(Colors.POPUP_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.POPUP_SELECTED, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(Colors.POPUP_BORDER, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.CORE_NUMBER, curses.COLOR_WHITE, curses.COLOR_BLACK)
            
            # Try to enhance colors if supported
            if curses.can_change_color():
                try:
                    curses.init_color(Colors.WHITE, 1000, 1000, 1000)    # Pure white
                    curses.init_color(Colors.RED, 1000, 400, 400)        # Bright red
                    curses.init_color(Colors.GREEN, 400, 1000, 400)      # Bright green
                    curses.init_color(Colors.YELLOW, 1000, 1000, 400)    # Bright yellow
                    curses.init_color(Colors.MAGENTA, 1000, 400, 1000)   # Bright magenta
                    curses.init_color(Colors.CYAN, 400, 1000, 1000)      # Bright cyan
                    curses.init_color(Colors.GRAY, 600, 600, 600)        # Medium gray
                    curses.init_color(Colors.ORANGE, 1000, 647, 0)       # Bright orange
                except curses.error:
                    pass
        else:
            # Black & white mode
            curses.init_pair(Colors.NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.SELECTED, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.HEADER, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.INFO, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.BORDER, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.FREQUENCY, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.GOVERNOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.EPP, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.POPUP_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.POPUP_SELECTED, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(Colors.POPUP_BORDER, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(Colors.CORE_NUMBER, curses.COLOR_WHITE, curses.COLOR_BLACK)

    def start(self):
        curses.wrapper(self.main)

    def main(self, stdscr):
        # Setup colors
        self.set_colors(stdscr)
        
        # Set default color and ensure black background
        stdscr.bkgd(' ', curses.color_pair(Colors.NORMAL))
        
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
            height = stdscr.getmaxyx()[0]
            visible_lines = height - 3
            
            if key == ord('q'):
                self.running = False
            elif key == ord(' '):
                self.selected_cores.symmetric_difference_update([self.current_row])
            elif key == curses.KEY_UP:
                if self.current_row > 0:
                    self.current_row -= 1
                    if self.current_row < self.scroll_position:
                        self.scroll_position = self.current_row
            elif key == curses.KEY_DOWN:
                if self.current_row < self.cpu_manager.cpu_cores - 1:
                    self.current_row += 1
                    if self.current_row >= self.scroll_position + visible_lines:
                        self.scroll_position = self.current_row - visible_lines + 1
            elif key == ord('j'):
                stdscr.nodelay(0)
                popup = NumberInput(stdscr, "Jump to Core", self.cpu_manager.cpu_cores - 1)
                selected = popup.show()
                stdscr.nodelay(1)
                if selected is not None:
                    self.current_row = selected
                    if self.current_row < self.scroll_position:
                        self.scroll_position = self.current_row
                    elif self.current_row >= self.scroll_position + visible_lines:
                        self.scroll_position = self.current_row - visible_lines + 1
                stdscr.clear()
            elif key == ord('a'):
                if len(self.selected_cores) == self.cpu_manager.cpu_cores:
                    self.selected_cores.clear()
                else:
                    self.selected_cores = set(range(self.cpu_manager.cpu_cores))
            elif key == ord('g'):
                stdscr.nodelay(0)
                popup = PopupMenu(stdscr, "Select Governor", self.cpu_manager.available_governors)
                selected = popup.show()
                stdscr.nodelay(1)
                if selected:
                    cores_to_update = self.selected_cores or {self.current_row}
                    self.cpu_manager.update_all_governors(selected, cores_to_update)
                stdscr.clear()
            elif key == ord('e') and self.amd_pstate_active:
                # Get EPP info from current core or first selected core
                core_id = next(iter(self.selected_cores)) if self.selected_cores else self.current_row
                info = self.cpu_manager.get_cpu_info(core_id)
                available_preferences = info.get('energy_performance_available_preferences', '').split()
                if available_preferences:
                    stdscr.nodelay(0)
                    popup = PopupMenu(stdscr, f"Select EPP Profile (Core {core_id})", available_preferences)
                    selected = popup.show()
                    stdscr.nodelay(1)
                    if selected:
                        cores_to_update = self.selected_cores or {self.current_row}
                        self.cpu_manager.update_all_epp(selected, list(cores_to_update))
                    stdscr.clear()
            elif key == ord('r'):
                stdscr.nodelay(0)
                popup = RefreshRateInput(stdscr, self.refresh_rate)
                new_rate = popup.show()
                stdscr.nodelay(1)
                if new_rate is not None:
                    self.refresh_rate = new_rate
                stdscr.clear()
            elif key == ord('z'):
                self.color_mode = not self.color_mode
                self.set_colors(stdscr)
                stdscr.clear()
        except curses.error:
            pass

    def safe_addstr(self, stdscr, y, x, text, attr=curses.A_NORMAL):
        """Safely add a string to the screen, truncating if necessary."""
        try:
            height, width = stdscr.getmaxyx()
            if y < 0 or x < 0 or y >= height or x >= width:
                return
            
            # Calculate remaining space
            remaining = width - x
            if remaining <= 0:
                return
            
            # Truncate text if necessary
            if len(text) > remaining:
                text = text[:remaining-1]
            
            # Try to add the string with attributes
            try:
                stdscr.addstr(y, x, text, attr)
            except curses.error:
                # If that fails, try without attributes
                try:
                    stdscr.addstr(y, x, text)
                except curses.error:
                    # If that still fails, try character by character
                    for i, char in enumerate(text):
                        if x + i >= width:
                            break
                        try:
                            stdscr.addch(y, x + i, char)
                        except curses.error:
                            break
        except:
            pass  # Ignore any errors in safe_addstr

    def update_display(self, stdscr):
        try:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # Draw box around the entire display (using ASCII characters for better compatibility)
            for y in range(height):
                for x in range(width):
                    if y == 0 and x == 0:
                        self.safe_addstr(stdscr, y, x, "+")
                    elif y == 0 and x == width-1:
                        self.safe_addstr(stdscr, y, x, "+")
                    elif y == height-1 and x == 0:
                        self.safe_addstr(stdscr, y, x, "+")
                    elif y == height-1 and x == width-1:
                        self.safe_addstr(stdscr, y, x, "+")
                    elif y == 0 or y == height-1:
                        self.safe_addstr(stdscr, y, x, "-")
                    elif x == 0 or x == width-1:
                        self.safe_addstr(stdscr, y, x, "|")
            
            # Display header (ensure it fits within bounds)
            header = " CPU Monitor (TUI) - Press 'q' to quit, 'space' to select, 'a' for all cores "
            header = header[:width-4]  # Leave space for borders
            header_pos = min((width - len(header)) // 2, width-len(header)-2)
            self.safe_addstr(stdscr, 0, header_pos, header, curses.A_BOLD | curses.color_pair(Colors.HEADER))
            
            # Display available actions
            actions = "Press 'g' for governor selection, 'j' to jump to core, 'r' to adjust refresh rate, 'z' to toggle colors"
            if self.amd_pstate_active:
                actions += ", 'e' for EPP profile selection"
            actions = actions[:width-4]  # Ensure it fits
            self.safe_addstr(stdscr, 1, 2, actions, curses.color_pair(Colors.INFO))
            
            # Calculate visible range based on scroll position
            visible_lines = height - 4  # Account for borders and headers
            start_idx = self.scroll_position
            end_idx = min(start_idx + visible_lines, self.cpu_manager.cpu_cores)
            
            # Draw separator line
            separator = "-" * (width-2)
            self.safe_addstr(stdscr, 2, 1, separator, curses.color_pair(Colors.BORDER))
            
            # Display core information
            for i in range(start_idx, end_idx):
                try:
                    info = self.cpu_manager.get_cpu_info(i)
                    y_pos = i - start_idx + 3
                    
                    # Base attributes for the line
                    base_attr = curses.color_pair(Colors.SELECTED) if i in self.selected_cores else curses.color_pair(Colors.NORMAL)
                    if i == self.current_row:
                        base_attr |= curses.A_REVERSE
                    
                    # Format each column with fixed width
                    x = 2  # Start position after left border
                    
                    # Core number (with fixed width)
                    core_text = f"Core {i:2d}"
                    self.safe_addstr(stdscr, y_pos, x, core_text, base_attr)
                    x += 8  # Fixed width for core number
                    
                    # Separator
                    self.safe_addstr(stdscr, y_pos, x, "|", curses.color_pair(Colors.BORDER))
                    x += 2
                    
                    # Frequency
                    freq_text = f"Freq: {self.format_frequency(info['frequency'])}"
                    self.safe_addstr(stdscr, y_pos, x, freq_text, base_attr | curses.color_pair(Colors.FREQUENCY))
                    x += 20  # Fixed width for frequency column
                    
                    # Separator
                    self.safe_addstr(stdscr, y_pos, x, "|", curses.color_pair(Colors.BORDER))
                    x += 2
                    
                    # Governor
                    gov_text = f"Gov: {info['governor']:<12}"
                    self.safe_addstr(stdscr, y_pos, x, gov_text, base_attr | curses.color_pair(Colors.GOVERNOR))
                    x += len(gov_text) + 2
                    
                    # EPP if available
                    if self.amd_pstate_active and x < width-20:  # Only if there's enough space
                        self.safe_addstr(stdscr, y_pos, x-2, "|", curses.color_pair(Colors.BORDER))
                        epp_text = f"EPP: {info.get('energy_performance_preference', 'N/A'):<8}"
                        self.safe_addstr(stdscr, y_pos, x, epp_text, base_attr | curses.color_pair(Colors.EPP))
                except Exception as e:
                    error_msg = f"Error displaying core {i}: {str(e)}"
                    error_msg = error_msg[:width-4]  # Ensure error message fits
                    self.safe_addstr(stdscr, y_pos, 2, error_msg, curses.color_pair(Colors.NORMAL))
            
            stdscr.refresh()
        except Exception as e:
            # If there's an error, try to display it
            try:
                stdscr.clear()
                error_msg = f"Display error: {str(e)}"
                error_msg = error_msg[:width-2]  # Ensure error message fits
                stdscr.addstr(0, 0, error_msg, curses.color_pair(Colors.NORMAL))
                stdscr.refresh()
            except:
                pass  # If we can't even display the error, just continue

    @property
    def amd_pstate_active(self):
        return self.cpu_manager.amd_pstate_active 