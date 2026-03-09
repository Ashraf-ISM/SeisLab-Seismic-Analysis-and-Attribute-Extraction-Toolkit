"""
Example Usage Script for SeisLab
Demonstrates programmatic usage of SeisLab components
"""

import numpy as np
import matplotlib.pyplot as plt

# Import SeisLab modules
from seismic.segy_loader import SegyLoader
from seismic.seismic_info import build_seismic_info
from attributes.rms import RMSAmplitude, Energy
from attributes.instantaneous import (InstantaneousAmplitude, 
                                      InstantaneousPhase,
                                      InstantaneousFrequency)
from processing.filters import BandpassFilter, GainControl, TraceNormalization
from ml.facies_classifier import classify_seismic_facies


def example_1_load_and_visualize():
    """Example 1: Load SEG-Y data and visualize."""
    print("Example 1: Loading and Visualizing Seismic Data")
    print("-" * 50)
    
    # Create loader (will use synthetic data if no file)
    loader = SegyLoader("synthetic_data.sgy")
    loader.load_data()
    
    # Get data info
    info = build_seismic_info(loader)
    print(f"Loaded data:")
    print(f"  Inlines: {info.n_inlines}")
    print(f"  Crosslines: {info.n_crosslines}")
    print(f"  Samples: {info.n_samples}")
    
    # Get inline section
    inline_data = loader.data[25, :, :]
    
    # Visualize
    plt.figure(figsize=(10, 6))
    plt.imshow(inline_data.T, aspect='auto', cmap='seismic')
    plt.colorbar(label='Amplitude')
    plt.title('Seismic Section - Inline 25')
    plt.xlabel('Trace Number')
    plt.ylabel('Time (samples)')
    plt.tight_layout()
    plt.savefig('example_1_seismic.png', dpi=150)
    print("Saved: example_1_seismic.png\n")
    plt.close()


def example_2_compute_attributes():
    """Example 2: Compute seismic attributes."""
    print("Example 2: Computing Seismic Attributes")
    print("-" * 50)
    
    # Load data
    loader = SegyLoader("synthetic_data.sgy")
    loader.load_data()
    inline_data = loader.data[25, :, :]
    
    # Compute RMS amplitude
    rms_calc = RMSAmplitude(window_size=25)
    rms_result = rms_calc.compute(inline_data)
    
    # Compute instantaneous amplitude
    inst_amp_calc = InstantaneousAmplitude()
    inst_amp_result = inst_amp_calc.compute(inline_data)
    
    # Compute instantaneous frequency
    inst_freq_calc = InstantaneousFrequency(sample_rate=2.0)
    inst_freq_result = inst_freq_calc.compute(inline_data)
    
    # Visualize
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Original
    im1 = axes[0, 0].imshow(inline_data.T, aspect='auto', cmap='seismic')
    axes[0, 0].set_title('Original Seismic')
    plt.colorbar(im1, ax=axes[0, 0])
    
    # RMS
    im2 = axes[0, 1].imshow(rms_result.T, aspect='auto', cmap='hot')
    axes[0, 1].set_title('RMS Amplitude')
    plt.colorbar(im2, ax=axes[0, 1])
    
    # Instantaneous Amplitude
    im3 = axes[1, 0].imshow(inst_amp_result.T, aspect='auto', cmap='hot')
    axes[1, 0].set_title('Instantaneous Amplitude')
    plt.colorbar(im3, ax=axes[1, 0])
    
    # Instantaneous Frequency
    im4 = axes[1, 1].imshow(inst_freq_result.T, aspect='auto', cmap='viridis')
    axes[1, 1].set_title('Instantaneous Frequency')
    plt.colorbar(im4, ax=axes[1, 1])
    
    plt.tight_layout()
    plt.savefig('example_2_attributes.png', dpi=150)
    print("Computed attributes:")
    print("  - RMS Amplitude")
    print("  - Instantaneous Amplitude")
    print("  - Instantaneous Frequency")
    print("Saved: example_2_attributes.png\n")
    plt.close()


def example_3_apply_filters():
    """Example 3: Apply signal processing filters."""
    print("Example 3: Applying Signal Processing Filters")
    print("-" * 50)
    
    # Load data
    loader = SegyLoader("synthetic_data.sgy")
    loader.load_data()
    inline_data = loader.data[25, :, :]
    
    # Apply bandpass filter
    bp_filter = BandpassFilter(lowcut=10, highcut=60, sample_rate=500)
    filtered_data = bp_filter.apply(inline_data)
    
    # Apply AGC
    agc = GainControl(gain_type='agc', window_size=50)
    agc_data = agc.apply(filtered_data)
    
    # Visualize
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Original
    im1 = axes[0].imshow(inline_data.T, aspect='auto', cmap='seismic')
    axes[0].set_title('Original')
    plt.colorbar(im1, ax=axes[0])
    
    # Bandpass filtered
    im2 = axes[1].imshow(filtered_data.T, aspect='auto', cmap='seismic')
    axes[1].set_title('Bandpass Filtered (10-60 Hz)')
    plt.colorbar(im2, ax=axes[1])
    
    # AGC applied
    im3 = axes[2].imshow(agc_data.T, aspect='auto', cmap='seismic')
    axes[2].set_title('AGC Applied')
    plt.colorbar(im3, ax=axes[2])
    
    plt.tight_layout()
    plt.savefig('example_3_processing.png', dpi=150)
    print("Applied filters:")
    print("  - Bandpass (10-60 Hz)")
    print("  - AGC (window=50)")
    print("Saved: example_3_processing.png\n")
    plt.close()


def example_4_ml_classification():
    """Example 4: Machine learning facies classification."""
    print("Example 4: Machine Learning Facies Classification")
    print("-" * 50)
    
    # Load data
    loader = SegyLoader("synthetic_data.sgy")
    loader.load_data()
    inline_data = loader.data[25, :, :]
    
    # Classify using multiple attributes
    facies_map = classify_seismic_facies(
        inline_data,
        method='kmeans',
        n_clusters=5,
        attributes=['amplitude', 'rms', 'inst_amp', 'inst_phase']
    )
    
    # Visualize
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Original
    im1 = axes[0].imshow(inline_data.T, aspect='auto', cmap='seismic')
    axes[0].set_title('Original Seismic')
    plt.colorbar(im1, ax=axes[0])
    
    # Facies classification
    im2 = axes[1].imshow(facies_map.T, aspect='auto', cmap='tab10')
    axes[1].set_title('Seismic Facies (K-Means, k=5)')
    plt.colorbar(im2, ax=axes[1], label='Facies Class')
    
    plt.tight_layout()
    plt.savefig('example_4_ml.png', dpi=150)
    print("Performed ML classification:")
    print("  - Method: K-Means")
    print("  - Clusters: 5")
    print("  - Attributes: amplitude, RMS, inst_amp, inst_phase")
    print("Saved: example_4_ml.png\n")
    plt.close()


def example_5_single_trace_analysis():
    """Example 5: Single trace analysis."""
    print("Example 5: Single Trace Analysis")
    print("-" * 50)
    
    # Load data
    loader = SegyLoader("synthetic_data.sgy")
    loader.load_data()
    
    # Get single trace
    trace = loader.data[25, 25, :]
    
    # Compute attributes for single trace
    rms_calc = RMSAmplitude(window_size=25)
    rms = rms_calc.compute(trace)
    
    inst_amp_calc = InstantaneousAmplitude()
    inst_amp = inst_amp_calc.compute(trace)
    
    # Visualize
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    
    time = np.arange(len(trace))
    
    # Original trace
    axes[0].plot(trace, time, 'k-', linewidth=1.5)
    axes[0].set_title('Original Trace')
    axes[0].set_xlabel('Amplitude')
    axes[0].set_ylabel('Time (samples)')
    axes[0].invert_yaxis()
    axes[0].grid(True, alpha=0.3)
    
    # RMS
    axes[1].plot(rms, time, 'r-', linewidth=1.5)
    axes[1].set_title('RMS Amplitude')
    axes[1].set_xlabel('RMS')
    axes[1].invert_yaxis()
    axes[1].grid(True, alpha=0.3)
    
    # Instantaneous Amplitude
    axes[2].plot(inst_amp, time, 'b-', linewidth=1.5)
    axes[2].set_title('Instantaneous Amplitude')
    axes[2].set_xlabel('Envelope')
    axes[2].invert_yaxis()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('example_5_trace.png', dpi=150)
    print("Analyzed single trace (25, 25)")
    print("  - Original amplitude")
    print("  - RMS amplitude")
    print("  - Instantaneous amplitude")
    print("Saved: example_5_trace.png\n")
    plt.close()


def run_all_examples():
    """Run all examples."""
    print("\n" + "="*60)
    print("SeisLab Usage Examples")
    print("="*60 + "\n")
    
    example_1_load_and_visualize()
    example_2_compute_attributes()
    example_3_apply_filters()
    example_4_ml_classification()
    example_5_single_trace_analysis()
    
    print("="*60)
    print("All examples completed successfully!")
    print("Check the generated PNG files for visualizations.")
    print("="*60)


if __name__ == "__main__":
    run_all_examples()
