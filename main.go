package main

import (
	"flag"
	"log"
	"math"
	"math/rand"
	"net"
	"strconv"

	"github.com/gonum/stat/combin"
)

var (
	size     int
	ebrbind  string
	databind string
	dest     string
)

func init() {
	flag.IntVar(&size, "size", 491, "Bytes in a packet")
	flag.StringVar(&ebrbind, "ebr", "127.0.0.1:4000", "Ebr information destination")
	flag.StringVar(&databind, "data", "127.0.0.1:4001", "Data information destination")
	flag.StringVar(&dest, "dest", "127.0.0.1:4040", "Where send destination")
}

type manager struct {
	errbitInfo  chan float64
	dataInfo    chan chan byte
	errbitJudge []float64
}

func newManager() *manager {
	return &manager{
		errbitInfo:  make(chan float64),
		dataInfo:    make(chan chan byte),
		errbitJudge: make([]float64, 4),
	}
}

func (m *manager) work() {
	bits := size * 8
	for {
		select {
		case ebr := <-m.errbitInfo:
			log.Printf("ebr update start: %v", ebr)
			for i := range m.errbitJudge {
				m.errbitJudge[i] = float64(combin.Binomial(bits, i)) * math.Pow(ebr, float64(i)) * math.Pow(1-ebr, float64(bits-i))
				if i != 0 {
					m.errbitJudge[i] += m.errbitJudge[i-1]
				}
			}
			m.errbitJudge[len(m.errbitJudge)-1] = 1
			log.Printf("ebr update ended")
		case fb := <-m.dataInfo:
			log.Printf("new data")
			dice := rand.Float64()
			for i := range m.errbitJudge {
				if dice < m.errbitJudge[i] {
					fb <- (1 << i) - 1
					log.Printf("error bits %v", i)
					break
				}
			}
		}
	}
}

func main() {
	ebrRecv, err := net.ListenPacket("udp", ebrbind)
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("read ebr info from %v", ebrbind)
	recv, err := net.ListenPacket("udp", databind)
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("read data info from %v", databind)
	send, err := net.Dial("udp", dest)
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("send data to %v", dest)
	m := newManager()
	go m.work()
	buf := make([]byte, 1024, 1024)
	sendBuf := make([]byte, size, size)
	for i := range sendBuf {
		sendBuf[i] = 0xff
	}
	generate := func() {
		fb := make(chan byte)
		defer close(fb)
		for {
			len, _, err := recv.ReadFrom(buf)
			if err != nil {
				log.Print(err)
				continue
			}
			log.Printf("read data length %v", len)
			m.dataInfo <- fb
			mask := <-fb
			sendBuf[0] = 0xff ^ mask
			send.Write(sendBuf)
		}
	}
	go generate()
	snrBuf := make([]byte, 1024, 1024)
	for {
		len, _, err := ebrRecv.ReadFrom(snrBuf)
		if err != nil {
			log.Print(err)
			continue
		}
		snr, err := strconv.ParseFloat(string(snrBuf[:len]), 64)
		if err != nil {
			log.Print(err)
			continue
		}
		m.errbitInfo <- snr
	}
}
