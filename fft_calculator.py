import numpy as np

def calculate_fft(signal, sampling_rate=1.0):
    """
    Calculate FFT coefficients from a signal.
    
    Args:
        signal (list or np.ndarray): Input signal
        sampling_rate (float): Sampling rate in Hz
    
    Returns:
        tuple: (frequencies, real coefficients, imaginary coefficients)
    """
    signal = np.array(signal)
    n = len(signal)
    
    # Compute FFT
    fft_result = np.fft.fft(signal)
    frequencies = np.fft.fftfreq(n, d=1/sampling_rate)
    
    # Get real and imaginary parts
    real_coeffs = fft_result.real
    imag_coeffs = fft_result.imag
    
    # Return positive frequencies only (up to Nyquist)
    nyquist_idx = n // 2
    return frequencies[:nyquist_idx], real_coeffs[:nyquist_idx], imag_coeffs[:nyquist_idx]


# def calculate_fft(signal, sampling_rate=1.0):
#     """
#     Calculate FFT coefficients from a signal.
    
#     Args:
#         signal (list or np.ndarray): Input signal
#         sampling_rate (float): Sampling rate in Hz
    
#     Returns:
#         tuple: (frequencies, real coefficients, imaginary coefficients)
#     """
#     signal = np.array(signal)
#     n = len(signal)
    
#     # Compute FFT
#     fft_result = np.fft.fft(signal)
#     frequencies = np.fft.fftfreq(n, d=1/sampling_rate)
    
#     # Get real and imaginary parts
#     real_coeffs = fft_result.real
#     imag_coeffs = fft_result.imag
    
#     # Return positive frequencies only (up to Nyquist)
#     nyquist_idx = n // 2
#     return frequencies[:nyquist_idx], real_coeffs[:nyquist_idx], imag_coeffs[:nyquist_idx]


def chunk_fft_data(real_coeffs, imag_coeffs, chunk_size=1000):
    """
    Split FFT coefficients into chunks for streaming.
    
    Args:
        real_coeffs (np.ndarray): Real FFT coefficients
        imag_coeffs (np.ndarray): Imaginary FFT coefficients
        chunk_size (int): Number of coefficients per chunk
    
    Yields:
        tuple: (chunk_id, real_chunk, imag_chunk, is_last_chunk)
    """
    n = len(real_coeffs)
    for i in range(0, n, chunk_size):
        is_last_chunk = (i + chunk_size) >= n
        yield (i // chunk_size,
               real_coeffs[i:i + chunk_size],
               imag_coeffs[i:i + chunk_size],
               is_last_chunk)