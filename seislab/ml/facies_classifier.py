"""
Machine Learning Module
Seismic facies classification using unsupervised learning
"""

import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler


class FaciesClassifier:
    """Unsupervised seismic facies classification."""
    
    def __init__(self, method='kmeans', n_clusters=5):
        """
        Initialize facies classifier.
        
        Args:
            method: Classification method ('kmeans', 'dbscan', 'gmm')
            n_clusters: Number of clusters/facies
        """
        self.method = method.lower()
        self.n_clusters = n_clusters
        self.model = None
        self.scaler = StandardScaler()
        
    def fit(self, attribute_matrix):
        """
        Fit classifier to attribute data.
        
        Args:
            attribute_matrix: 2D array (samples x attributes)
        """
        # Standardize features
        X_scaled = self.scaler.fit_transform(attribute_matrix)
        
        # Initialize and fit model
        if self.method == 'kmeans':
            self.model = KMeans(n_clusters=self.n_clusters, 
                               random_state=42, n_init=10)
            self.model.fit(X_scaled)
            
        elif self.method == 'dbscan':
            self.model = DBSCAN(eps=0.5, min_samples=5)
            self.model.fit(X_scaled)
            
        elif self.method == 'gmm':
            self.model = GaussianMixture(n_components=self.n_clusters,
                                        random_state=42)
            self.model.fit(X_scaled)
            
        else:
            raise ValueError(f"Unknown method: {self.method}")
            
    def predict(self, attribute_matrix):
        """
        Predict facies labels.
        
        Args:
            attribute_matrix: 2D array (samples x attributes)
            
        Returns:
            1D array of cluster labels
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
            
        # Standardize features
        X_scaled = self.scaler.transform(attribute_matrix)
        
        # Predict
        if self.method in ['kmeans', 'dbscan']:
            labels = self.model.fit_predict(X_scaled)
        elif self.method == 'gmm':
            labels = self.model.predict(X_scaled)
            
        return labels
        
    def fit_predict(self, attribute_matrix):
        """
        Fit and predict in one step.
        
        Args:
            attribute_matrix: 2D array (samples x attributes)
            
        Returns:
            1D array of cluster labels
        """
        self.fit(attribute_matrix)
        return self.predict(attribute_matrix)


class AttributeExtractor:
    """Extract multiple attributes for ML classification."""
    
    def __init__(self):
        """Initialize attribute extractor."""
        self.attributes = []
        
    def extract_from_section(self, data, attribute_list=None):
        """
        Extract multiple attributes from seismic section.
        
        Args:
            data: 2D seismic data array
            attribute_list: List of attributes to extract
            
        Returns:
            2D array (samples x attributes)
        """
        if attribute_list is None:
            attribute_list = ['amplitude', 'inst_amp', 'inst_phase', 'rms']
            
        from attributes.rms import RMSAmplitude
        from attributes.instantaneous import (InstantaneousAmplitude,
                                             InstantaneousPhase)
        
        n_traces, n_samples = data.shape
        n_points = n_traces * n_samples
        
        features = []
        
        for attr_name in attribute_list:
            if attr_name == 'amplitude':
                attr_data = data.flatten()
                
            elif attr_name == 'rms':
                calculator = RMSAmplitude(window_size=25)
                attr_data = calculator.compute(data).flatten()
                
            elif attr_name == 'inst_amp':
                calculator = InstantaneousAmplitude()
                attr_data = calculator.compute(data).flatten()
                
            elif attr_name == 'inst_phase':
                calculator = InstantaneousPhase()
                attr_data = calculator.compute(data).flatten()
                
            else:
                continue
                
            features.append(attr_data)
            
        # Stack features
        feature_matrix = np.column_stack(features)
        
        return feature_matrix


def classify_seismic_facies(data, method='kmeans', n_clusters=5, 
                           attributes=None):
    """
    Convenience function for seismic facies classification.
    
    Args:
        data: 2D seismic data array
        method: Classification method
        n_clusters: Number of facies
        attributes: List of attributes to use
        
    Returns:
        2D array of facies labels (same shape as input)
    """
    # Extract attributes
    extractor = AttributeExtractor()
    features = extractor.extract_from_section(data, attributes)
    
    # Classify
    classifier = FaciesClassifier(method=method, n_clusters=n_clusters)
    labels = classifier.fit_predict(features)
    
    # Reshape to original dimensions
    n_traces, n_samples = data.shape
    facies_map = labels.reshape(n_traces, n_samples)
    
    return facies_map
