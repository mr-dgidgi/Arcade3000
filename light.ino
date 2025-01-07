// LED Controlling for Arcade3000 Cabinet

// Array to store each light with : [pin][brightness]
int Lights[3][2] = {
    {3,0},
    {5,0},
    {6,0}
};

// intensity level step (5 = 255/5 = 51 intensity level)
const int fadeAmount = 5;

void setup() {
    // Configurer la broche LED comme sortie
    for(i=0;i<3;i++) {
        pinMode(Lights[i][0], OUTPUT);
    }
    for(i=0;i<3;i++) {
        pinMode(Lights[i][0], OUTPUT);
        analogWrite(ledPin, brightness);
    }
}

void loop() {
    for(i=0;i<3;i++) {
        int brightness = random(0,25)
        pinMode(Lights[i][brightness*10], OUTPUT);
        analogWrite(ledPin, brightness*10);
    }
  // slowing the loop
  delay(500);
}