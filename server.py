import asyncio
import json
import logging
import tornado.web
import tornado.websocket
import time
import random
from datetime import datetime, timedelta

now = time.time()

#creo dizionario con tutte le info di tutte le partite
#vinci il set con almeno 11 punti e 2 di vantaggio.

Partite = {
    "1": {
        "start": now - 697,  # 11:37 già trascorsi
        "stato": "live",
        "scheduled_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "punteggi": {"Paolo Rossi": [7, 0, 0, 0, 0], "Mario Pizza": [4, 0, 0, 0, 0]}        #punti di ogni giocatore per ogni set
    },
    "2": {
        "start": now - 2407,  # 40:07 già trascorsi
        "stato": "live",
        "scheduled_at": (datetime.now() - timedelta(minutes=40)).strftime("%Y-%m-%d %H:%M"),
        "punteggi": {"Anna Verdi": [12, 11, 7, 0, 0], "Sara Bianchi": [10, 13, 11, 0, 0]}
    },
    "3": {
        "tempo": {"ore": 1, "minuti": 15, "secondi": 57},   #durata partita
        "stato": "programmato",
        "scheduled_at": (datetime.now() + timedelta(hours=1, minutes=30)).strftime("%Y-%m-%d %H:%M"),
        "punteggi": {"Luca Neri": [0, 0, 0, 0, 0], "Marco Blu": [0, 0, 0, 0, 0]}
    },
    "4": {
        "tempo": {"ore": 1, "minuti": 5, "secondi": 2},     #durata partita
        "stato": "terminato",
        "scheduled_at": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
        "punteggi": {"Giulia Gialli": [11, 7, 11, 9, 15], "Elena Viola": [5, 11, 8, 11, 13]}
    },
    "5": {
        "tempo": {"ore": 0, "minuti": 42, "secondi": 30},       #durata partita
        "stato": "terminato",
        "scheduled_at": (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
        "punteggi": {"Mango Tropical": [13, 11, 7, 11, 0], "Mela Verde": [11, 9, 11, 8, 0]}
    }
}


def calcola_set_vinti(punteggi):

    #players = list(punteggi.keys())
    scores = list(punteggi.values()) #dizionario con giocatori e i loro punteggi per ogni set

    #punteggi dei due giocatori
    set_p1 = 0
    set_p2 = 0

    #scorre i 5 set, scores[0]=player1 scores[1]=player2
    for i in range(5):
        p1_score = scores[0][i]
        p2_score = scores[1][i]

        if p1_score >= 11 and p1_score - p2_score >= 2: #se giocatore1 ha 11 punti ed è in vantaggio di 2 punti allora ha vinto il set
            set_p1 += 1

        elif p2_score >= 11 and p2_score - p1_score >= 2:
            set_p2 += 1

    return set_p1, set_p2


def get_set_corrente(punteggi):

    scores = list(punteggi.values()) #dizionario con giocatori e i loro punteggi per ogni set

    #scorro i 5 set
    for i in range(5):
        p1_score = scores[0][i]
        p2_score = scores[1][i]

        # Se il set non è ancora stato vinto (condizioni usate nella funzione sopra), controllo se uno dei due giocatori ha fatto almeno un punto,
        # così so che è il set corrente e restituisco il set
        if not ((p1_score >= 11 and p1_score - p2_score >= 2) or
                (p2_score >= 11 and p2_score - p1_score >= 2)):

            if p1_score > 0 or p2_score > 0:
                return i

    return None


def aggiungi_punto_casuale(partita):

    players = list(partita["punteggi"].keys())
    scores = list(partita["punteggi"].values())

    # Trova il set corrente: primo set non ancora vinto da nessuno
    set_corrente = None
    for i in range(5):
        p1_score = scores[0][i]
        p2_score = scores[1][i]
        set_finito = ((p1_score >= 11 and p1_score - p2_score >= 2) or
                      (p2_score >= 11 and p2_score - p1_score >= 2))
        if not set_finito:
            set_corrente = i
            break

    # Nessun set corrente: tutti i set sono finiti
    if set_corrente is None:

        # Verifico se sono stati giocati tutti i 5 set o se qualcuno ha vinto 3 set
        set_p1, set_p2 = calcola_set_vinti(partita["punteggi"])

        if set_p1 >= 3 or set_p2 >= 3 or (set_p1 + set_p2) == 5: #se uno dei due giocatori ha vinto 3 set oppure se si sta giocando il 5 set(che è all'indice4)
            # Partita terminata
            trascorso = int(time.time() - partita['start'])
            ore = trascorso // 3600
            minuti = (trascorso % 3600) // 60
            secondi = trascorso % 60

            partita['stato'] = 'terminato'
            partita['tempo'] = {"ore": ore, "minuti": minuti, "secondi": secondi}
            del partita['start']

        return

    # Aggiungi il punto a un giocatore casuale
    giocatore_che_segna = random.randint(0, 1)
    partita["punteggi"][players[giocatore_che_segna]][set_corrente] += 1

    # Controlla se qualcuno ha vinto 3 set dopo l'aggiornamento e chiudi
    set_p1, set_p2 = calcola_set_vinti(partita["punteggi"])

    if set_p1 == 3 or set_p2 == 3:
        trascorso = int(time.time() - partita['start'])
        partita['tempo'] = {
            "ore": trascorso // 3600,
            "minuti": (trascorso % 3600) // 60,
            "secondi": trascorso % 60
        }
        partita['stato'] = 'terminato'

        giocatori = list(partita["punteggi"].keys())
        if set_p1 == 3:
            partita['winner'] = giocatori[0]
        else:
            partita['winner'] = giocatori[1]

        del partita['start']

    # Log: id partita, chi ha segnato, numero set (1..5) e punteggio set aggiornato
    print(
        f"Partita {list(Partite.keys())[list(Partite.values()).index(partita)]}: "
        f"{players[giocatore_che_segna]} segna! "
        f"Set {set_corrente + 1}: {scores[0][set_corrente]} - {scores[1][set_corrente]}"
    )


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("inizio.html", partite=Partite)


class InfoHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("info.html")


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    # Registro dei client attivi per broadcast. (è un insieme Python quindi contiene elementi unici che non possono comparire due volte)
    clients = set()

    def open(self):
        print("WebSocket connesso")
        WebSocketHandler.clients.add(self)

        # invio al client l'id delle partite
        for partita_id in Partite.keys():
            self.send_partita_data(partita_id)

    def on_close(self):
        print("WebSocket disconnesso")
        WebSocketHandler.clients.discard(self)

    def on_message(self, message):
        data = json.loads(message)

        #Quando arriva un messaggio dal client, se è una richiesta “getMatch” con un “matchId”,
        # il server risponde inviando al client i dati aggiornati della partita con quell’ID.

        if data.get('action') == 'getMatch' and data.get('matchId'):
            self.send_partita_data(data['matchId'])

    def send_partita_data(self, partita_id):


        if partita_id not in Partite:
            return

        #se la partita è presente nel dizionario delle partite prendo il dizionario della partita, i giocatori e i loro punteggi
        partita = Partite[partita_id]
        players = list(partita["punteggi"].keys())
        scores = list(partita["punteggi"].values())

        #calcolo i set vinti dei giocatori e trovo il set che si sta giocando ora
        set_p1, set_p2 = calcola_set_vinti(partita["punteggi"])
        set_corrente = get_set_corrente(partita["punteggi"])

        # Prepara i dati dei set completati
        sets_data = {}

        #per ogni set
        for i in range(5):
            p1_score = scores[0][i]
            p2_score = scores[1][i]

            # Verifica se il set è completato (True/False)
            is_completed = ((p1_score >= 11 and p1_score - p2_score >= 2) or
                            (p2_score >= 11 and p2_score - p1_score >= 2))

            #mette i dati nel dizioanrio del set(i)
            sets_data[f'set{i + 1}'] = {
                'p1': p1_score,
                'p2': p2_score,
                'completed': is_completed
            }

        # Dati set corrente
        dati_set_durante = None

        if set_corrente is not None:
            dati_set_durante = {
                'p1': scores[0][set_corrente],
                'p2': scores[1][set_corrente],
                'setNumber': set_corrente + 1
            }

        #dizionario con tutti i dati della partita
        message = {
            'matchId': partita_id,
            'player1': players[0],
            'player2': players[1],
            'setsP1': set_p1,
            'setsP2': set_p2,
            'stato': partita['stato'],
            'sets': sets_data,
            'current': dati_set_durante,
            'scheduledAt': partita.get('scheduled_at')
        }

        # Aggiungi il tempo
        if partita['stato'] == 'live':
            trascorso = int(time.time() - partita['start'])
            ore = trascorso // 3600
            minuti = (trascorso % 3600) // 60
            secondi = trascorso % 60
            message['time'] = f"{ore:02}:{minuti:02}:{secondi:02}" #02 serve per mettere i numeri a due cifre (5 --> 05)

        elif partita['stato'] == 'terminato' or partita['stato'] == 'programmato':
            tempo = partita['tempo']
            message['time'] = f"{tempo['ore']:02}:{tempo['minuti']:02}:{tempo['secondi']:02}"

        try:
            self.write_message(json.dumps(message))
        except tornado.websocket.WebSocketClosedError:
            pass


async def simula_partite():

    while True:
        # Ogni tot secondi aggiungo un punto a una partita live
        await asyncio.sleep(random.uniform(1, 3))

        # Trova tutte le partite live
        partite_live = []
        for partita_id, partita in Partite.items():
            if partita['stato'] == 'live':
                partite_live.append((partita_id, partita))

        if partite_live:
            # Scegli una partita live casuale

            partita_id, partita = random.choice(partite_live)

            # Aggiungi un punto casuale
            aggiungi_punto_casuale(partita)

            # broadcast a tutti i client connessi
            for client in WebSocketHandler.clients:
                client.send_partita_data(partita_id)



async def broadcast_live_updates():

    while True:

        await asyncio.sleep(1) #così ogni secondo viene inviato il messaggio con il tempo trascorso al client (quindi fa funzionare il timer?)

        for partita_id, partita in Partite.items():

            if partita['stato'] == 'live':

                players = list(partita["punteggi"].keys())
                scores = list(partita["punteggi"].values())

                set_p1, set_p2 = calcola_set_vinti(partita["punteggi"])

                trascorso = int(time.time() - partita['start'])
                ore = trascorso // 3600
                minuti = (trascorso % 3600) // 60
                secondi = trascorso % 60

                messaggio = {
                    'matchId': partita_id,
                    'player1': players[0],
                    'player2': players[1],
                    'setsP1': set_p1,
                    'setsP2': set_p2,
                    'time': f"{ore:02}:{minuti:02}:{secondi:02}",
                    'stato': 'live',
                    'scheduledAt': partita.get('scheduled_at') #ora in cui è iniziata la partita
                }

                if 'winner' in partita:
                    messaggio['winner'] = partita['winner'] #aggiunto se la partita è terminata



                # broadcast a tutti i client connessi
                for client in WebSocketHandler.clients:
                    client.write_message(json.dumps(messaggio))


async def main():
    logging.basicConfig(level=logging.INFO)

    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/info.html", InfoHandler),
            (r"/ws", WebSocketHandler)
        ],
        template_path="",
    )

    app.listen(8888)
    print("Server Tornado avviato su http://localhost:8888")

    # Avvia il broadcast degli aggiornamenti live (timer 1s)
    asyncio.create_task(broadcast_live_updates())

    # Avvia la simulazione dei punteggi (sleep 1-3s)
    asyncio.create_task(simula_partite())

    # Mantiene il loop in vita indefinitamente
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())