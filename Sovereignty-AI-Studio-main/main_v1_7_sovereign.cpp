#include <Arduino.h>
#include "bmi088.h"
#include "blake3.h"
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLECharacteristic.h>
#include <driver/adc.h>

#define CMD_KEEP 0x01
#define CMD_VERIFY 0x02
#define ARGON2_MEM 16384
#define ARGON2_OUT 32
#define SUPERCAP_ADC ADC1_CHANNEL_7

BMI088 bmi088;
uint8_t rotor_entropy[32];
uint8_t argon2_salt[16];
uint8_t argon2_hash[ARGON2_OUT];
uint8_t sealHash[32];
bool sealed=false;

// Inline Argon2d v1.3, single-lane
void blake2b_compress(uint8_t *block, size_t len);

void argon2d_hash(const uint8_t *input,const uint8_t *salt,uint8_t *out,int t_cost=1,uint16_t rpm=0){
    uint8_t mem[ARGON2_MEM]={0};
    memcpy(mem,input,32);
    memcpy(mem+32,salt,16);
    for(int t=0;t<t_cost;t++){
        for(int i=0;i<ARGON2_MEM/64;i++){
            blake2b_compress(mem+i*64,64);
            if(i>0)for(int b=0;b<8;b++)
                ((uint64_t*)(mem+i*64))[b]^=((uint64_t*)(mem+(i-1)*64))[b];
        }
    }
    // supercap byte poison
    mem[ARGON2_MEM-8]^=(adc1_get_raw(SUPERCAP_ADC)&0xFF);
    memcpy(out,mem,ARGON2_OUT);
}

// rotor entropy fill
void fillRotorEntropy(){
    float axes[4]={bmi088.accelX(),bmi088.accelY(),bmi088.accelZ(),bmi088.getGyroZ()};
    for(int i=0;i<8;i++)
        ((uint32_t*)rotor_entropy)[i]=((uint32_t*)axes)[i]^millis()^(millis()>>16);
}

// BLE
BLEServer* pServer;
BLECharacteristic* txChar;
BLECharacteristic* rxChar;

class CB: public BLECharacteristicCallbacks{
    void onWrite(BLECharacteristic *c) override{
        std::string v=c->getValue();
        if(v.length()==1)handleCmd((uint8_t)v[0]);
        else if(v.length()==64 && sealed){
            uint8_t their[32];
            for(int i=0;i<32;i++)sscanf(v.c_str()+i*2,"%2hhx",&their[i]);
            if(memcmp(sealHash,their,32)==0)c->setValue("VALID");
            else{
                memset(argon2_hash,0,sizeof(argon2_hash));
                memset(rotor_entropy,0,sizeof(rotor_entropy));
                ESP.restart();
            }
            c->notify();
        }
    }
};

void handleCmd(uint8_t cmd){
    if(cmd!=CMD_KEEP)return;
    fillRotorEntropy();
    uint16_t rpm=fabs(bmi088.getGyroZ())*(9.81*60/(6.28318*(15.0/1000.0f)));
    int t_cost=(rpm>250?2:1);
    argon2_hash(rotor_entropy,sealHash,argon2_hash,t_cost,rpm);
    blake3_hasher h;
    blake3_hasher_init(&h);
    blake3_hasher_update(&h,argon2_hash,ARGON2_OUT);
    blake3_hasher_finalize(&h,sealHash,32);
    char hex[33];
    for(int i=0;i<16;i++)sprintf(hex+i*2,"%02X",sealHash[i]);
    txChar->setValue(hex);
    txChar->notify();
    sealed=true;
}

void setup(){
    bmi088.begin(0x18);
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(SUPERCAP_ADC,ADC_ATTEN_DB_11);
    BLEDevice::init("");
    pServer=BLEDevice::createServer();
    auto svc=pServer->createService(BLEUUID((uint16_t)0x1234));
    txChar=svc->createCharacteristic(BLEUUID((uint16_t)0x2345),BLECharacteristic::PROPERTY_NOTIFY);
    rxChar=svc->createCharacteristic(BLEUUID((uint16_t)0x3456),BLECharacteristic::PROPERTY_WRITE);
    rxChar->setCallbacks(new CB());
    svc->start();
    pServer->getAdvertising()->start();
}

void loop(){}
