package main

import (
	"flag"
	"fmt"
	"log"
	"math"
	"math/rand"
	"net"
	"strconv"
	"time"

	"github.com/gonum/stat/combin"
)

var (
	size      int
	ebrbind   string
	databind  string
	dest      string
	mode      string
	duration  int
	packetNum int
	ebr       float64
)

type manager struct {
	errbitInfo  chan float64
	dataInfo    chan chan byte
	errbitJudge []float64
}

func newManager() *manager {
	return &manager{
		errbitInfo:  make(chan float64),
		dataInfo:    make(chan chan byte),
		errbitJudge: []float64{1, 0, 0, 0},
	}
}

func (m *manager) work() {
	bits := size * 8
	for {
		select {
		case ebr := <-m.errbitInfo:
			ebr *= 0.9
			if ebr < 1e-8 {
				m.errbitJudge[0] = 1
				break
			}
			for i := range m.errbitJudge {
				m.errbitJudge[i] = float64(combin.Binomial(bits, i)) * math.Pow(ebr, float64(i)) * math.Pow(1-ebr, float64(bits-i))
				if i != 0 {
					m.errbitJudge[i] += m.errbitJudge[i-1]
				}
			}
			m.errbitJudge[len(m.errbitJudge)-1] = 1
		case fb := <-m.dataInfo:
			dice := rand.Float64()
			for i := range m.errbitJudge {
				if dice < m.errbitJudge[i] {
					fb <- (1 << i) - 1
					break
				}
			}
		}
	}
}

func main() {
	flag.StringVar(&mode, "mode", "normal", "normal/sender/receiver/setebr")
	flag.IntVar(&size, "size", 491, "Bytes in a packet")
	flag.StringVar(&ebrbind, "ebr", "127.0.0.1:4000", "Ebr information destination")
	flag.StringVar(&databind, "data", "127.0.0.1:4001", "Data information destination")
	flag.StringVar(&dest, "dest", "127.0.0.1:4040", "Where send destination")
	flag.IntVar(&duration, "duration", 1000, "duration between 2 packets(only use in sender)")
	flag.IntVar(&packetNum, "packet", 20000, "packet number")
	flag.Float64Var(&ebr, "ebr_value", 1e-5, "ebr(only use in set ebr)")
	flag.Parse()
	log.Printf("runing mode %v", mode)
	switch mode {
	case "normal":
		normal()
	case "sender":
		sender()
	case "receiver":
		receiver()
	case "setebr":
		setEbr()
	default:
		log.Fatal("unknown mode")
	}
}

func setEbr() {
	conn, err := net.Dial("udp", ebrbind)
	if err != nil {
		log.Fatalf("setebr %v", err)
	}
	out := fmt.Sprintf("%v", ebr)
	log.Printf("ebr value %v", ebr)
	conn.Write([]byte(out))
}

func sender() {
	conn, err := net.Dial("udp", databind)
	if err != nil {
		log.Fatal(err)
	}
	buf := make([]byte, size, size)
	buildHead := func() {
		for i := 0; i < size; i++ {
			if i < 100 {
				buf[i] = 0
			} else {
				buf[i] = 0x0f
			}
		}
	}
	buildTail := func() {
		for i := 0; i < size; i++ {
			if i < 100 {
				buf[i] = 0
			} else {
				buf[i] = 0xff
			}
		}
	}
	send := func() {
		conn.Write(buf)
		time.Sleep(time.Duration(duration) * time.Microsecond)
	}
	for i := 0; i < 3; i++ {
		buildHead()
		send()
	}
	for i := 0; i < size; i++ {
		buf[i] = 0xff
	}
	for i := 0; i < packetNum; i++ {
		send()
	}
	for i := 0; i < 3; i++ {
		buildTail()
		send()
	}
}

func countOne(input byte) int {
	result := 0
	for input != 0 {
		result++
		input = input - (input & (-input))
	}
	return result
}

func receiver() {
	recv, err := net.ListenPacket("udp", dest)
	if err != nil {
		log.Fatal(err)
	}
	state := "ready"
	frameCount := 0
	errorFrame := 0
	errorBits := 0
	buf := make([]byte, size, size)
	for {
		recv.ReadFrom(buf)
		headZero := 0
		for i := 0; i < 100; i++ {
			if buf[i] == 0 {
				headZero++
			}
		}
		tailOne := 0
		for i := size - 100; i < size; i++ {
			if buf[i] == 0xff {
				tailOne++
			}
		}
		if headZero > 50 {
			if tailOne < 50 {
				state = "running"
				frameCount = 0
				errorFrame = 0
				errorBits = 0
			} else if state == "running" {
				state = "ready"
				log.Printf("total frame %v, errframe %v, efr %v", frameCount, errorFrame, float64(errorFrame)/float64(frameCount))
				log.Printf("total bits %v, errbits %v, ebr %v", frameCount*size*8, errorBits, float64(errorBits)/float64(frameCount*8*size))
			}
		} else {
			currentErrorbits := 0
			for i := range buf {
				currentErrorbits += countOne(buf[i] ^ 0xff)
			}
			errorBits += currentErrorbits
			if currentErrorbits != 0 {
				errorFrame++
			}
			frameCount++
		}
	}
}

func normal() {
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
	destAddress, err := net.ResolveUDPAddr("udp", dest)
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
			_, _, err := recv.ReadFrom(buf)
			if err != nil {
				log.Print(err)
				continue
			}
			headZero := 0
			for i := 0; i < 100; i++ {
				if buf[i] == 0 {
					headZero++
				}
			}
			if headZero > 50 {
				recv.WriteTo(buf[:size], destAddress)
				continue
			}
			m.dataInfo <- fb
			mask := <-fb
			sendBuf[0] = 0xff ^ mask
			recv.WriteTo(sendBuf, destAddress)
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
		log.Printf("read ebr %v", snr)
		if err != nil {
			log.Print(err)
			continue
		}
		m.errbitInfo <- snr
	}
}
