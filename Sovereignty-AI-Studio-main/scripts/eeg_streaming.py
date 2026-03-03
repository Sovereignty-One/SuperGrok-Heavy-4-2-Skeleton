import time 
import csv
import os
import numpy as np
from pylsl import StreamInlet, resolve_byprop
from scipy.signal import butter, lfilter, welch
from datetime import datetime
from scipy.integrate import trapezoid
import threading
import pandas as pd
import joblib
import subprocess
from pathlib import Path
import json
from collections import Counter
import asyncio
import queue

# ==============================
# REAL-TIME BROADCASTING SYSTEM
# ==============================

# Global queue for real-time data broadcasting
eeg_broadcast_queue = queue.Queue(maxsize=50)

# Store for latest EEG data (for polling endpoints)
latest_eeg_data = {
    'timestamp': None,
    'delta': 0,
    'theta': 0,
    'alpha': 0,
    'beta': 0,
    'gamma': 0,
    'label': 'N/A',
    'relative': {
        'delta_rel': 0,
        'theta_rel': 0,
        'alpha_rel': 0,
        'beta_rel': 0,
        'gamma_rel': 0
    },
    'artifacts': False
}

# Lock for thread-safe updates
eeg_data_lock = threading.Lock()

# Active SSE connections (for broadcasting)
active_eeg_clients = set()

def broadcast_eeg_data(data_dict):
    """
    Broadcast EEG data to all connected SSE clients
    """
    try:
        # Update latest data
        with eeg_data_lock:
            latest_eeg_data.update(data_dict)
            latest_eeg_data['timestamp'] = datetime.now().isoformat()
        
        # Add to broadcast queue (non-blocking)
        try:
            eeg_broadcast_queue.put_nowait(data_dict)
        except queue.Full:
            # Remove oldest if queue is full
            try:
                eeg_broadcast_queue.get_nowait()
                eeg_broadcast_queue.put_nowait(data_dict)
            except:
                pass
        
        return True
    except Exception as e:
        print(f"❌ Broadcast error: {e}")
        return False

def get_latest_eeg_data():
    """Get the latest EEG data safely"""
    with eeg_data_lock:
        return latest_eeg_data.copy()

def clear_eeg_broadcast():
    """Clear broadcast queue"""
    while not eeg_broadcast_queue.empty():
        try:
            eeg_broadcast_queue.get_nowait()
        except:
            break
    with eeg_data_lock:
        latest_eeg_data.update({
            'timestamp': None,
            'delta': 0,
            'theta': 0,
            'alpha': 0,
            'beta': 0,
            'gamma': 0,
            'label': 'N/A',
            'relative': {
                'delta_rel': 0,
                'theta_rel': 0,
                'alpha_rel': 0,
                'beta_rel': 0,
                'gamma_rel': 0
            },
            'artifacts': False
        })

# ==============================
# GLOBAL STREAMING STATE
# ==============================

streaming_state = {
    'status': 'idle',
    'message': '',
    'elapsed_time': 0,
    'total_duration': 0,
    'current_label': 'N/A',
    'device_connected': False,
    'output_filename': '',
    'student_name': '',
    'teacher_name': '',
    'arid_no': '',
    'student_video_path': '',
    'teacher_video_path': '',
    'latest_eeg': latest_eeg_data,  # Reference to latest data
    'samples_collected': 0
}

streaming_thread = None
should_stop = False
is_paused = False

# Frequency bands
bands = {
    'Delta': (0.5, 4),
    'Theta': (4, 8),
    'Alpha': (8, 12),
    'Beta': (12, 30),
    'Gamma': (30, 100)
}

# ==============================
# EEG PROCESSING FUNCTIONS
# ==============================

def normalize_to_relative_powers(delta, theta, alpha, beta, gamma):
    """Convert absolute powers to relative percentages (0-1 scale)."""
    epsilon = 1e-6
    total = delta + theta + alpha + beta + gamma + epsilon
    
    return {
        'delta_rel': delta / total,
        'theta_rel': theta / total,
        'alpha_rel': alpha / total,
        'beta_rel': beta / total,
        'gamma_rel': gamma / total,
        'total_power': total
    }

def is_artifact(delta, theta, alpha, beta, gamma):
    """NO ARTIFACT DETECTION - all samples get model predictions!"""
    return False  # Never mark anything as Unknown

def start_muse_stream():
    """Start muselsl stream automatically."""
    try:
        print("🚀 Launching muselsl stream...")
        
        # Kill any existing muselsl processes first
        try:
            import sys
            if sys.platform == "win32":
                os.system('taskkill /f /im muselsl.exe 2>nul')
                os.system('taskkill /f /im python.exe /fi "WINDOWTITLE eq muselsl*" 2>nul')
            else:
                os.system('pkill -f muselsl 2>/dev/null')
            time.sleep(2)
        except:
            pass
        
        # Start muselsl stream
        subprocess.Popen(
            "muselsl stream",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("🎧 muselsl stream started successfully!")
        
    except Exception as e:
        print("❌ Could not start muselsl stream:", e)
        raise

def bandpower(data, fs, band):
    """Calculate band power using Welch's method"""
    fmin, fmax = band
    freqs, psd = welch(data, fs=fs, nperseg=min(256, len(data)))
    idx_band = np.logical_and(freqs >= fmin, freqs <= fmax)
    return trapezoid(psd[idx_band], freqs[idx_band])

def butter_bandpass_filter(data, lowcut, highcut, fs, order=4):
    """Standard bandpass filter for EEG signals"""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return lfilter(b, a, data)

# ==============================
# REAL-TIME STREAMING FUNCTION WITH BROADCASTING
# ==============================

def stream_eeg_data(student_name, teacher_name, arid_no, duration):
    global streaming_state, should_stop, is_paused
    
    # Clear previous broadcast data
    clear_eeg_broadcast()

    try:
        # Start muselsl
        streaming_state['status'] = 'connecting'
        streaming_state['message'] = 'Starting muselsl stream...'
        streaming_state['student_name'] = student_name
        streaming_state['teacher_name'] = teacher_name
        streaming_state['arid_no'] = arid_no
        
        try:
            start_muse_stream()
        except Exception as e:
            streaming_state['status'] = 'error'
            streaming_state['message'] = f'Failed to start muselsl: {str(e)}'
            print(f"❌ muselsl start error: {e}")
            return

        print("⏳ Waiting for Muse stream (5 seconds)...")
        time.sleep(5)

        print("🔍 Searching EEG stream...")
        streams = resolve_byprop('type', 'EEG', timeout=30)

        if not streams:
            streaming_state['status'] = 'error'
            streaming_state['message'] = 'No EEG device found. Make sure Muse is connected.'
            print("❌ No EEG stream found.")
            return

        inlet = StreamInlet(streams[0])
        streaming_state['device_connected'] = True
        streaming_state['status'] = 'recording'
        streaming_state['message'] = 'Device connected! Recording and broadcasting data...'

        print("✅ EEG stream connected.")
        print("📊 Real-time streaming ACTIVE - data will be broadcast live!")
        print("🌐 Frontend can connect via: /api/eeg/live")

        # Get current working directory
        current_dir = Path.cwd()
        output_dir = current_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        print(f"📁 Output directory: {output_dir}")

        # Create session directory
        session_folder = f"{student_name}_{arid_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_path = output_dir / session_folder
        session_path.mkdir(exist_ok=True)

        # EEG filename
        eeg_filename = session_path / f"{student_name}_{arid_no}_EEG.csv"
        streaming_state['output_filename'] = str(eeg_filename)

        # Store video paths
        streaming_state['student_video_path'] = str(session_path / f"{student_name}_{arid_no}_student.webm")
        streaming_state['teacher_video_path'] = str(session_path / f"{teacher_name}_{student_name}_{arid_no}_teacher.webm")

        sampling_rate = 256
        window_size = 1
        buffer_size = sampling_rate * window_size

        sample, _ = inlet.pull_sample()
        channel_count = len(sample)
        buffers = [[] for _ in range(channel_count)]

        print(f"⏺ Recording for {duration} seconds...")
        print(f"📁 Session folder: {session_path}")
        print(f"📡 Broadcasting data every second...")

        # Store raw data for ML processing
        raw_data_buffer = []

        with open(eeg_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time", "Delta", "Theta", "Alpha", "Beta", "Gamma", "Label"])

            start_time = time.time()
            next_second = start_time + 1
            sample_count = 0

            while streaming_state['elapsed_time'] < duration:

                if should_stop:
                    streaming_state['status'] = 'stopped'
                    streaming_state['message'] = 'Stopped by user'
                    print("⏹ Stopped by user")
                    break

                if is_paused:
                    time.sleep(0.1)
                    continue

                sample, _ = inlet.pull_sample(timeout=1.0)
                if sample is None:
                    continue

                for i in range(channel_count):
                    buffers[i].append(sample[i])
                    if len(buffers[i]) > buffer_size:
                        buffers[i] = buffers[i][-buffer_size:]

                current_time = time.time()
                streaming_state['elapsed_time'] = int(current_time - start_time)

                if current_time >= next_second:

                    if all(len(buf) >= buffer_size for buf in buffers):
                        band_powers = {b: [] for b in bands}

                        for buf in buffers:
                            filtered = butter_bandpass_filter(buf, 1, 60, sampling_rate)

                            for band_name, freq_range in bands.items():
                                bp = bandpower(filtered, sampling_rate, freq_range)
                                band_powers[band_name].append(bp)

                        averaged = {b: round(np.mean(v), 2) for b, v in band_powers.items()}
                        timestamp_str = datetime.now().strftime('%H:%M:%S')
                        
                        # Calculate relative powers for monitoring
                        rel = normalize_to_relative_powers(
                            averaged['Delta'], averaged['Theta'], 
                            averaged['Alpha'], averaged['Beta'], averaged['Gamma']
                        )
                        
                        # Store raw data for later ML processing
                        raw_data_buffer.append({
                            'Time': timestamp_str,
                            'Delta': averaged['Delta'],
                            'Theta': averaged['Theta'],
                            'Alpha': averaged['Alpha'],
                            'Beta': averaged['Beta'],
                            'Gamma': averaged['Gamma'],
                            'Label': ''
                        })

                        # Write raw data with empty Label (will be filled later)
                        writer.writerow([
                            timestamp_str,
                            averaged['Delta'],
                            averaged['Theta'],
                            averaged['Alpha'],
                            averaged['Beta'],
                            averaged['Gamma'],
                            ''
                        ])

                        # ============================================
                        # REAL-TIME BROADCASTING
                        # ============================================
                        broadcast_data = {
                            'timestamp': timestamp_str,
                            'delta': float(averaged['Delta']),
                            'theta': float(averaged['Theta']),
                            'alpha': float(averaged['Alpha']),
                            'beta': float(averaged['Beta']),
                            'gamma': float(averaged['Gamma']),
                            'label': 'N/A',  # Will be updated after ML
                            'relative': {
                                'delta_rel': float(rel['delta_rel']),
                                'theta_rel': float(rel['theta_rel']),
                                'alpha_rel': float(rel['alpha_rel']),
                                'beta_rel': float(rel['beta_rel']),
                                'gamma_rel': float(rel['gamma_rel'])
                            },
                            'artifacts': is_artifact(
                                averaged['Delta'], averaged['Theta'], 
                                averaged['Alpha'], averaged['Beta'], averaged['Gamma']
                            ),
                            'sample_count': sample_count,
                            'elapsed_seconds': streaming_state['elapsed_time'],
                            'total_duration': duration,
                            'progress_percentage': int((streaming_state['elapsed_time'] / duration) * 100)
                        }
                        
                        # Broadcast to all connected clients
                        broadcast_eeg_data(broadcast_data)
                        
                        sample_count += 1
                        streaming_state['samples_collected'] = sample_count

                        # Console output
                        print(
                            f"{timestamp_str} 📡 | "
                            f"Δ:{averaged['Delta']:6.0f} Θ:{averaged['Theta']:6.0f} "
                            f"α:{averaged['Alpha']:6.0f} β:{averaged['Beta']:6.0f} γ:{averaged['Gamma']:7.0f} | "
                            f"β%:{rel['beta_rel']*100:3.0f} α%:{rel['alpha_rel']*100:3.0f} δ%:{rel['delta_rel']*100:3.0f}"
                        )

                    next_second += 1

        print(f"\n📊 Recording complete! {len(raw_data_buffer)} samples collected")
        print("📡 Stopping real-time broadcast...")

        # ==============================
        # ML MODEL PROCESSING - NO UNKNOWN LABELS
        # ==============================
        try:
            print("\n🤖 Processing ALL EEG data with ML model - NO Unknown labels!")
            
            model_path = Path("RandomForest.pkl")
            if not model_path.exists():
                print("❌ Model file 'RandomForest.pkl' not found.")
                streaming_state['status'] = 'error'
                streaming_state['message'] = 'Model file not found'
                return
                
            # Load ML model
            print("✅ Loading ML model...")
            bundle = joblib.load(str(model_path))

            if isinstance(bundle, dict):
                model = bundle.get("model")
                scaler = bundle.get("scaler", None)
                print(f"✅ Model loaded: {type(model).__name__}")
                if scaler:
                    print("✅ Scaler loaded")
            else:
                model = bundle
                scaler = None
                print(f"✅ Model loaded: {type(model).__name__}")

            # Prepare ALL data for model prediction
            all_data_for_model = []
            
            for row in raw_data_buffer:
                all_data_for_model.append([
                    row['Delta'],
                    row['Theta'],
                    row['Alpha'],
                    row['Beta'],
                    row['Gamma']
                ])
            
            print(f"📊 Total samples: {len(all_data_for_model)}")
            
            if len(all_data_for_model) > 0:
                if scaler is not None:
                    X = scaler.transform(all_data_for_model)
                else:
                    X = all_data_for_model

                # Get model predictions for ALL data
                print("🔮 Running model predictions on ALL samples...")
                model_predictions = model.predict(X)

                # Map numeric predictions to labels
                label_map = {
                    0: "Very Low",
                    1: "Low", 
                    2: "Medium",
                    3: "High",
                    4: "Very High"
                }

                # Apply model predictions to ALL data - NO Unknown labels!
                all_labels = []
                for idx, (row, model_pred) in enumerate(zip(raw_data_buffer, model_predictions)):
                    model_label = label_map.get(int(model_pred), "Very Low")  # Default to "Very Low" if unknown mapping
                    row['Label'] = model_label
                    all_labels.append(model_label)
                
                # Calculate final label distribution
                label_counts = Counter(all_labels)
                
                print(f"\n📊 FINAL label distribution (ALL samples labeled):")
                for label in ["Very Low", "Low", "Medium", "High", "Very High"]:
                    count = label_counts.get(label, 0)
                    percentage = (count / len(raw_data_buffer)) * 100
                    print(f"   {label:10s}: {count:3d} samples ({percentage:5.1f}%)")
                
                # Determine most common label
                if label_counts:
                    most_common = label_counts.most_common(1)[0][0]
                    streaming_state['current_label'] = most_common
                    
                    # Update latest data with final label
                    with eeg_data_lock:
                        latest_eeg_data['label'] = most_common
                    
                    print(f"\n🎯 Most common cognitive load: {most_common}")
                
                print(f"✅ All {len(raw_data_buffer)} samples labeled successfully!")
                
            else:
                print("⚠️ No data for ML processing")
                streaming_state['message'] = 'Recording completed (no data)'
                
        except Exception as err:
            print(f"❌ ML processing error: {err}")
            import traceback
            traceback.print_exc()
            
            # FALLBACK: If ML fails, assign "Medium" to all samples
            print("🔄 ML failed - assigning 'Medium' to all samples as fallback")
            for row in raw_data_buffer:
                row['Label'] = "Medium"
            
            streaming_state['current_label'] = "Medium"
            print(f"✅ Fallback: All {len(raw_data_buffer)} samples labeled as 'Medium'")

        # ==============================
        # REWRITE CSV WITH FINAL LABELS
        # ==============================
        print("\n💾 Saving final EEG data with labels...")
        
        with open(eeg_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time", "Delta", "Theta", "Alpha", "Beta", "Gamma", "Label"])
            
            for row in raw_data_buffer:
                writer.writerow([
                    row['Time'],
                    row['Delta'],
                    row['Theta'],
                    row['Alpha'],
                    row['Beta'],
                    row['Gamma'],
                    row['Label']
                ])
        
        file_size = os.path.getsize(eeg_filename)
        print(f"✅ Final EEG file saved: {eeg_filename} ({file_size} bytes)")
        print(f"📋 Sample of labels: {[row['Label'] for row in raw_data_buffer[:5]]}...")

        # ==============================
        # CREATE SESSION METADATA
        # ==============================
        metadata_file = session_path / "session_metadata.json"
        
        # Calculate statistics
        label_counts = Counter([row['Label'] for row in raw_data_buffer])
        
        metadata = {
            "student_name": student_name,
            "teacher_name": teacher_name,
            "arid_no": arid_no,
            "duration": duration,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "eeg_file": str(eeg_filename),
            "student_video": streaming_state['student_video_path'],
            "teacher_video": streaming_state['teacher_video_path'],
            "samples_collected": len(raw_data_buffer),
            "final_cognitive_load": streaming_state.get('current_label', 'Medium'),
            "label_distribution": dict(label_counts),
            "processing_method": "ml_model_only_no_unknown",
            "ml_model": model_path.name if 'model' in locals() else None,
            "model_type": type(model).__name__ if 'model' in locals() else "Fallback",
            "real_time_broadcast": True
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"📄 Metadata saved → {metadata_file}")
        
        # Print final summary
        print(f"\n📋 FINAL SESSION SUMMARY:")
        print(f"   Total samples: {len(raw_data_buffer)}")
        print(f"   Final prediction: {streaming_state.get('current_label', 'Medium')}")
        
        print(f"\n   Label Distribution (100% labeled):")
        for label in ["Very Low", "Low", "Medium", "High", "Very High"]:
            count = label_counts.get(label, 0)
            if count > 0:
                percentage = (count / len(raw_data_buffer)) * 100
                print(f"     {label:10s}: {count:3d} ({percentage:5.1f}%)")

        streaming_state['status'] = 'completed'
        streaming_state['message'] = f'Session completed! {len(raw_data_buffer)} samples analyzed.'

        # Send final broadcast with completion status
        final_broadcast = {
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'message': f'Session completed with {len(raw_data_buffer)} samples',
            'final_label': streaming_state.get('current_label', 'Medium'),
            'total_samples': len(raw_data_buffer)
        }
        broadcast_eeg_data(final_broadcast)

    except Exception as e:
        streaming_state['status'] = 'error'
        streaming_state['message'] = f'Error: {str(e)[:100]}'
        print(f"❌ ERROR in stream_eeg_data: {e}")
        import traceback
        traceback.print_exc()

# ==============================
# API WRAPPERS
# ==============================
def start_streaming(student_name, teacher_name, arid_no, duration):
    global streaming_thread, should_stop, is_paused, streaming_state

    should_stop = False
    is_paused = False

    streaming_state = {
        'status': 'connecting',
        'message': 'Starting...',
        'elapsed_time': 0,
        'total_duration': duration,
        'current_label': 'N/A',
        'device_connected': False,
        'output_filename': '',
        'student_name': student_name,
        'teacher_name': teacher_name,
        'arid_no': arid_no,
        'student_video_path': '',
        'teacher_video_path': '',
        'samples_collected': 0
    }

    streaming_thread = threading.Thread(
        target=stream_eeg_data,
        args=(student_name, teacher_name, arid_no, duration),
        daemon=True
    )
    streaming_thread.start()

    return {'success': True, 'message': 'Streaming started'}

def pause_streaming():
    global is_paused
    is_paused = True
    streaming_state['status'] = 'paused'
    
    # Send pause broadcast
    pause_data = {
        'timestamp': datetime.now().isoformat(),
        'status': 'paused',
        'message': 'Streaming paused'
    }
    broadcast_eeg_data(pause_data)
    
    return {'success': True}

def resume_streaming():
    global is_paused
    is_paused = False
    streaming_state['status'] = 'recording'
    
    # Send resume broadcast
    resume_data = {
        'timestamp': datetime.now().isoformat(),
        'status': 'recording',
        'message': 'Streaming resumed'
    }
    broadcast_eeg_data(resume_data)
    
    return {'success': True}

def stop_streaming():
    global should_stop
    should_stop = True
    
    # Send stop broadcast
    stop_data = {
        'timestamp': datetime.now().isoformat(),
        'status': 'stopped',
        'message': 'Streaming stopped by user'
    }
    broadcast_eeg_data(stop_data)
    
    return {'success': True}

def get_streaming_status():
    # Add progress percentage and latest data
    enhanced_status = streaming_state.copy()
    if streaming_state['total_duration'] > 0:
        enhanced_status['progress_percentage'] = min(100, 
            int((streaming_state['elapsed_time'] / streaming_state['total_duration']) * 100))
    else:
        enhanced_status['progress_percentage'] = 0
        
    enhanced_status['time_remaining'] = max(0, 
        streaming_state['total_duration'] - streaming_state['elapsed_time'])
    
    # Add latest EEG data
    enhanced_status['latest_eeg'] = get_latest_eeg_data()
    
    # Add broadcast status
    enhanced_status['broadcasting'] = streaming_state['status'] == 'recording'
    enhanced_status['clients_connected'] = len(active_eeg_clients)
    
    return enhanced_status

def save_video_file(video_data, video_type, student_name, teacher_name, arid_no):
    """
    Save uploaded video file to the session folder
    video_type: 'student' or 'teacher'
    """
    try:
        current_dir = Path.cwd()
        output_dir = current_dir / "output"
        
        # Find the most recent session folder for this student
        session_folders = [f for f in output_dir.iterdir() if f.is_dir() and f.name.startswith(f"{student_name}_{arid_no}")]
        
        if not session_folders:
            return {'success': False, 'error': 'Session folder not found'}
        
        # Get the most recent folder
        latest_session = max(session_folders, key=lambda x: x.stat().st_ctime)
        
        if video_type == 'student':
            filename = f"{student_name}_{arid_no}_student.webm"
        else:
            filename = f"{teacher_name}_{student_name}_{arid_no}_teacher.webm"
        
        filepath = latest_session / filename
        
        with open(filepath, 'wb') as f:
            f.write(video_data)
        
        print(f"✅ {video_type.capitalize()} video saved → {filepath}")
        return {'success': True, 'path': str(filepath)}
        
    except Exception as e:
        print(f"❌ Error saving {video_type} video:", e)
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def reset_streaming():
    global streaming_state, should_stop, is_paused
    should_stop = False
    is_paused = False
    streaming_state = {
        'status': 'idle',
        'message': '',
        'elapsed_time': 0,
        'total_duration': 0,
        'current_label': 'N/A',
        'device_connected': False,
        'output_filename': '',
        'student_name': '',
        'teacher_name': '',
        'arid_no': '',
        'student_video_path': '',
        'teacher_video_path': '',
        'samples_collected': 0
    }
    
    # Clear broadcast data
    clear_eeg_broadcast()
    
    return {'success': True}

# ==============================
# SSE BROADCASTING FUNCTIONS
# ==============================

async def eeg_sse_generator():
    """Generator for Server-Sent Events EEG data"""
    # Create a queue for this client
    client_queue = asyncio.Queue(maxsize=10)
    client_id = id(client_queue)
    active_eeg_clients.add(client_queue)
    
    print(f"🎮 New EEG client connected: {client_id}")
    
    try:
        # Send initial connection message
        yield {
            "event": "connected",
            "data": {
                "client_id": client_id,
                "message": "Connected to EEG stream",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Main loop for sending data
        while True:
            try:
                # Get data from broadcast queue (with timeout)
                data = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: eeg_broadcast_queue.get(timeout=2.0)
                )
                
                # Format as SSE event
                yield {
                    "event": "eeg_data",
                    "data": data
                }
                
            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield {
                    "event": "heartbeat",
                    "data": {"timestamp": datetime.now().isoformat()}
                }
                
            except asyncio.CancelledError:
                print(f"🎮 EEG client disconnected: {client_id}")
                break
                
    except Exception as e:
        print(f"❌ SSE generator error for client {client_id}: {e}")
    finally:
        # Cleanup
        active_eeg_clients.discard(client_queue)
        print(f"🎮 EEG client cleanup: {client_id}")

# ==============================
# UTILITY FUNCTIONS FOR FRONTEND
# ==============================

def get_eeg_broadcast_queue():
    """Get the broadcast queue for external access"""
    return eeg_broadcast_queue

def get_active_clients_count():
    """Get number of active SSE clients"""
    return len(active_eeg_clients)

def is_broadcasting():
    """Check if EEG is currently broadcasting"""
    return streaming_state['status'] == 'recording'

# Add this to your __all__ if you have one
__all__ = [
    'start_streaming',
    'pause_streaming',
    'resume_streaming',
    'stop_streaming',
    'get_streaming_status',
    'save_video_file',
    'reset_streaming',
    'broadcast_eeg_data',
    'get_latest_eeg_data',
    'eeg_sse_generator',
    'get_eeg_broadcast_queue',
    'get_active_clients_count',
    'is_broadcasting'
]
