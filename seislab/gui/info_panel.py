"""
Info Panel
Display file and data information
"""

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class InfoPanel(QGroupBox):
    """Panel for displaying file information."""
    
    def __init__(self):
        super().__init__("File Information")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Info labels
        self.label_file = QLabel("File: Not loaded")
        self.label_inlines = QLabel("Inlines: -")
        self.label_crosslines = QLabel("Crosslines: -")
        self.label_samples = QLabel("Samples: -")
        self.label_rate = QLabel("Sample Rate: -")
        
        # Style labels
        for label in [self.label_file, self.label_inlines, 
                     self.label_crosslines, self.label_samples, 
                     self.label_rate]:
            label.setWordWrap(True)
            label.setStyleSheet("""
                QLabel {
                    padding: 4px;
                    color: #424242;
                    font-size: 11px;
                }
            """)
        
        layout.addWidget(self.label_file)
        layout.addWidget(self.label_inlines)
        layout.addWidget(self.label_crosslines)
        layout.addWidget(self.label_samples)
        layout.addWidget(self.label_rate)
        
    def update_info(self, info_dict):
        """
        Update displayed information.
        
        Args:
            info_dict: Dictionary with file information
        """
        import os
        
        filename = os.path.basename(info_dict.get('filepath', 'Unknown'))
        self.label_file.setText(f"<b>File:</b> {filename}")
        
        n_inlines = info_dict.get('n_inlines', 0)
        self.label_inlines.setText(f"<b>Inlines:</b> {n_inlines}")
        
        n_crosslines = info_dict.get('n_crosslines', 0)
        self.label_crosslines.setText(f"<b>Crosslines:</b> {n_crosslines}")
        
        n_samples = info_dict.get('n_samples', 0)
        self.label_samples.setText(f"<b>Samples:</b> {n_samples}")
        
        sample_rate = info_dict.get('sample_rate', 0)
        self.label_rate.setText(f"<b>Sample Rate:</b> {sample_rate:.2f} ms")
