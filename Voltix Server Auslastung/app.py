from flask import Flask, render_template, jsonify
import psutil

app = Flask(__name__)

# Anzahl der logischen CPU-Kerne (wichtig für die 100%-Rechnung)
CPU_CORES = psutil.cpu_count()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats')
def stats():
    # interval=0.1 verhindert, dass 0.0 zurückgegeben wird
    cpu = psutil.cpu_percent(interval=0.1)
    return jsonify({
        'cpu_usage': cpu,
        'ram_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    })

@app.route('/processes/<sort_by>')
def processes(sort_by):
    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            p_info = proc.info
            
            # CPU-Wert auf 100% normieren (geteilt durch Kerne)
            raw_cpu = p_info['cpu_percent'] if p_info['cpu_percent'] else 0.0
            p_info['cpu_percent'] = round(raw_cpu / CPU_CORES, 1)
            
            # Speicher auf 1 Nachkommastelle
            p_info['memory_percent'] = round(p_info['memory_percent'], 1)
            
            # PID als Integer sicherstellen
            p_info['pid'] = int(p_info['pid'])
            
            procs.append(p_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    sort_key = 'cpu_percent' if sort_by == 'cpu' else 'memory_percent'
    top_procs = sorted(procs, key=lambda x: x[sort_key], reverse=True)[:10]
    
    return jsonify(top_procs)

if __name__ == '__main__':
    # host='0.0.0.0' macht es im Netzwerk unter deiner IP erreichbar
    app.run(host='0.0.0.0', port=5000, debug=False)