import flet as ft
import numpy as np
import pandas as pd
import math

class Graphic:
    def __init__(self):
        self.path = ""
        self.table = None

    def setPath(self, path):
        self.path = path
        if self.path != "":
            tabelaTESF = pd.read_excel(self.path)
            self.setTable(table=tabelaTESF)

    def setTable(self, table):
        self.table = table

    def getTable(self):
        return self.table

    def getBottomAxis(self):
        labels = []
        for i in range(0, len(self.table["Data_Hora"])):
            t_str = self.table["Data_Hora"][i].strftime('%Y-%m-%d %H:%M:%S')
            hour = t_str.split()[1].split(":")[0]
            minute = t_str.split()[1].split(":")[1]
            if minute == '00':
                labels.append(ft.ChartAxisLabel(value = i, label=ft.Text(f"{hour}:{minute}", size=10)))
        return labels

    def generateDataSeriesRadiance(self):
        labels = []
        for i in range(0,len(self.table["Radiação"])):
            labels.append(
                ft.LineChartDataPoint(i, float(self.table["Radiação"][i]))
            )
        return labels
    
    def getMaxRadiance(self):
        return max(self.table["Radiação"])
    
    def getMaxTemperature(self):
        return max(self.table["Temp_Cel"])
    
    def getLeftAxisRadiance(self):
        labels = []
        for i in range(0, int(self.getMaxYRadiance()+1)):
            if i%100 == 0:
                labels.append(
                    ft.ChartAxisLabel(
                        value = i,
                        label=ft.Text(f"{i}", size=10),
                    )
                )
        return labels
    
    def generateDataSeriesTemperature(self):
        labels = []
        for i in range(0,len(self.table["Temp_Cel"])):
            labels.append(
                ft.LineChartDataPoint(i, float(self.table["Temp_Cel"][i]))
            )
        return labels

    def getLeftAxisTemperature(self):
        labels = []
        for i in range(0, int(self.getMaxYTemperature()+1)):
            if i%10 == 0:
                labels.append(
                    ft.ChartAxisLabel(
                        value = i,
                        label=ft.Text(f"{i}", size=10),
                    )
                )
        return labels

    def getListHours(self):
        list = []
        for t in self.table["Data_Hora"]:
            list.append(ft.dropdown.Option(t.strftime("%H:%M")))
        return list

    def getMinYRadiance(self):
        return -1
    
    def getMaxYRadiance(self):
        r = max(self.table["Radiação"]) % 100
        if r > 0:
            return max(self.table["Radiação"]) + (100-r)
        return max(self.table["Radiação"])
        
    def getMinYTemperature(self):
        return min(self.table["Temp_Cel"])-10
    
    def getMaxYTemperature(self):
        return max(self.table["Temp_Cel"])+1
    
    def getMinX(self):
        return -1
    
    def getMaxX(self):
        return len(self.table["Data_Hora"])+1

g = Graphic()

g.setPath("/home/ronaldocandido/Downloads/TESF-main/TabelaTESF.xlsx")

class PhotovoltaicCell:
    def __init__(self, table, time):
        self.table = table
        self.time = time
        self.I = []
        self.V = []
        self.pot = []
        self.Is = 0
        self.vLim = 0
        self.timer = []
        self.Voltage = []
        self.Current = []
        self.numPlacas = 0
        self.theta = np.pi
        self.frequencyangle = np.pi
        self.P1 = []
        self.P2 = []
        self.P3 = []

    def setTime(self, time):
        self.time, time

    def constant_two(self,VMPP, IMPP, VOC, ISC):
        return ((VMPP / VOC - 1) / np.log(1 - IMPP / ISC))

    def constant_one(self,VMPP, IMPP, VOC, ISC):
        return (1 - IMPP / ISC) * np.exp((-1 * VMPP) / (self.constant_two(VMPP, IMPP, VOC, ISC) * VOC))

    # Calcula a corrente do módulo fotovoltaico (FV)
    def IP(self,VP, VMPP, IMPP, VOC, ISC):
        return ISC * (1 - self.constant_one(VMPP, IMPP, VOC, ISC) * (np.exp(VP / (self.constant_two(VMPP, IMPP, VOC, ISC) * VOC) )- 1))

    # Calcula corrente de curto-circuito
    def ISC(self,G,T,ISCS,alpha,GS = 1000, TS = 298):
        return ISCS*(G/GS)*(1+alpha*(T-TS))

    # Calcula tensão de circuito aberto
    def VOC(self,T,beta,VOCS,TS = 298):
        return VOCS + (T-273)*beta*(T-TS)

    # Calcula Corrente no ponto de máxima potência(MPP)
    def IMPP(self,G,T,IMPPS,alpha,GS = 1000, TS = 298):
        return IMPPS*(G/GS)*(1+alpha*(T-TS))

    # Calcula Tensão no ponto de máxima potência(MPP)
    def VMPP(self,T,beta,VMPPS,TS = 298):
        return VMPPS + (T-273)*beta*(T-TS)

    def searchDates(self,time):
        for i in range(0, len(self.table['Data_Hora'])):
            if self.table['Data_Hora'][i].strftime("%H:%M") == time:
                return self.table['Radiação'][i], self.table['Temp_Cel'][i]
        return None

    def searchDate(self,time):
        for i in range(0, len(self.table['Data_Hora'])):
            if self.table['Data_Hora'][i].strftime("%H:%M") == time:
                return self.table['Data_Hora'][i]

    def calcRadiance(self, time, irradiancia_global, beta, gamma_p, lat, long_local, long_meridiano, horario_verao=0):
        # Convertendo a string da data e hora para objeto datetime com o novo formato
        data_hora = self.searchDate(time)
        dia = data_hora.timetuple().tm_yday

        # Determinando a equação do tempo (em horas)
        B = (360/365) * (dia - 81)
        EoT = 9.87 * np.sin(np.radians(2*B)) - 7.53 * np.cos(np.radians(B)) - 1.5 * np.sin(np.radians(B))
        EoT /= 60  # Convertendo para horas

        # Hora local
        hora_local = data_hora.hour + data_hora.minute / 60

        # Calculando a hora solar
        hora_solar = hora_local - ((long_local - long_meridiano) / 15) + EoT + horario_verao

        # Calculando a declinação solar
        declinacao_solar = 23.45 * np.sin(np.radians(360 * (284 + dia) / 365))

        # Calculando o ângulo horário
        omega = 15 * (hora_solar - 12)

        # Calculando o ângulo zenital do sol
        theta_z = np.degrees(np.arccos(np.sin(np.radians(lat)) * np.sin(np.radians(declinacao_solar)) +
                                        np.cos(np.radians(lat)) * np.cos(np.radians(declinacao_solar)) * np.cos(np.radians(omega))))

        # Calculando o azimute solar
        gamma_solar = np.degrees(np.arctan2(np.sin(np.radians(omega)),
                                                np.cos(np.radians(omega)) * np.sin(np.radians(lat)) -
                                                np.tan(np.radians(declinacao_solar)) * np.cos(np.radians(lat))))

        # Cálculo do ângulo de incidência
        theta_i = np.degrees(np.arccos(np.sin(np.radians(theta_z)) * np.cos(np.radians(gamma_p - gamma_solar)) * np.sin(np.radians(beta)) +
                                            np.cos(np.radians(theta_z)) * np.cos(np.radians(beta))))

        # Cálculo da irradiância incidente
        return irradiancia_global * np.cos(np.radians(theta_i))

    def calcPanel(self, G, T):
        T = T+273
        # Coeficientes de temperatura
        alpha = 0.0005  # Coeficiente de Corrente (0.05% / °C)
        beta = -0.0026  # Coeficiente de Tensão (-0.26% / °C)

        # Parâmetros do painel CS7L-605MS
        ISCS_R = 18.52
        VOCS_R = 41.5  # Tensão de Circuito Aberto (V)
        IMPPS_R = 17.25  # Corrente no Ponto de Máxima Potência (A)
        VMPPS_R = 35.1  # Tensão no Ponto de Máxima Potência (V)

        # Calculando os parâmetros com base em G e T
        ISCS = self.ISC(G, T, ISCS_R, alpha, GS=1000, TS=298)
        VOCS = self.VOC(T, beta, VOCS_R, TS=298)
        IMPPS = self.IMPP(G, T, IMPPS_R, alpha, GS=1000, TS=298)
        VMPPS = self.VMPP(T, beta, VMPPS_R, TS=298)

        # Faixa de valores de tensão (V)
        V_range = np.linspace(0, VOCS, 1000)

        # Calcula as correntes correspondentes para cada valor de tensão
        I_values = [self.IP(V, VMPPS, IMPPS, VOCS, ISCS) for V in V_range]

        return  I_values, V_range, ISCS, VOCS

    def getValues(self):
        radiacao, tempCelula = self.searchDates(self.time)
        parameters = pd.read_excel("parametersTESF.xlsx")
        lat = -9.55766947266527
        long_local = -35.78090672062049
        long_meridiano = -45
        beta = int(parameters["beta"][0])
        gamma_p = int(parameters["gamma_p"][0])
        # lat = float(parameters["lat"][0])
        # long_local = float(parameters["long_local"][0])
        # long_meridiano = float(parameters["long_meridiano"][0])
        horario_verao = int(parameters["horario_verao"][0])
        numPlacas = int(parameters["numPlacas"][0])
        theta = eval(parameters["theta"][0])
        frequencyangle = eval(parameters["frequencyangle"][0])
        gIncidence = self.calcRadiance(self.time, radiacao, beta, gamma_p, lat, long_local, long_meridiano, horario_verao)
        I, V, Is, vLim = self.calcPanel(gIncidence, tempCelula)
        self.I = I
        self.V = V
        self.Is = Is
        self.vLim = vLim
        self.numPlacas = numPlacas
        self.theta = theta
        self.frequencyangle = frequencyangle
        self.timer = np.linspace(0, 0.02, 1000)
        self.setVoltageCurrent()
        self.getPot()

    def setVoltageCurrent(self):
        potRede = self.numPlacas * 17.25 * 35.1
        Vp = 35.1 * self.numPlacas * np.sqrt(2)  # Tensão de pico
        Ip = 2*potRede/Vp  # Corrente de pico (ajuste conforme necessário)
        w = 2 * self.theta * 60  # Frequência angular (60 Hz)
        labelsVoltage = []
        labelsCurrent =[]
        labelsP1 = []
        labelsP2 = []
        labelsP3 = []
        cos = np.cos(self.theta)
        if cos < 0.000000001 and cos > -0.000000001:
            cos = 0

        for i in self.timer:
            labelsVoltage.append(Vp * np.cos(w * i))
            labelsCurrent.append(Ip * np.cos(w * i - self.theta))
            labelsP1.append(((Vp* Ip)/2 * (np.cos(2*w * i)))*cos + (Vp* Ip)/2*cos)
            labelsP2.append(i * Vp * np.cos(w * i))
            labelsP3.append(((Vp* Ip)/2)*np.sin(2*w * i)*np.sin(self.theta))
        self.Voltage = labelsVoltage
        self.Current = labelsCurrent
        self.P1 = labelsP1
        self.P2 = labelsP2
        self.P3 = labelsP3

    def getPot(self):
        l = []
        for i in range(0,len(self.I)):
            l.append(self.I[i]*self.V[i])
        self.pot = l

    def getId(self):
        for i in range(0,len(self.I)):
            if self.pot[i] == max(self.pot):
                return self.I[i], self.V[i]

    def generateIV(self):
        labels = []
        for i in range(0,len(self.I)):
            labels.append(
                ft.LineChartDataPoint(self.V[i], self.I[i])
            )
        return labels

    def generatePIV(self):
        labels = []
        for i in range(0,len(self.I)):
            pot = self.V[i]*self.I[i]
            pot = ((self.getMaxYPIV()-2)*pot)/max(self.pot)
            labels.append(
                ft.LineChartDataPoint(self.V[i], pot)
            )
        return labels
    
    def getLeftAxisPIV(self):
        return [
            ft.ChartAxisLabel(value = self.getMinYPIV(), label = ft.Text(f"{self.getMinYPIV()}", size = 10)),
            ft.ChartAxisLabel(value = self.Is, label = ft.Text(f"{self.Is}", size = 10)),
            # ft.ChartAxisLabel(value = 0, label = ft.Text("0", size = 10)), # Máxima Potência para dps
            ft.ChartAxisLabel(value = self.getMaxYPIV(), label = ft.Text(f"{self.getMaxYPIV()}A", size = 10)),
        ]
    
    def getBottomAxisPIV(self):
        return [
            ft.ChartAxisLabel(value = self.getMinXPIV(), label = ft.Text(f"{self.getMinXPIV()}", size = 10)),
            ft.ChartAxisLabel(value = self.vLim, label = ft.Text(f"{self.vLim}", size = 10)),
            # ft.ChartAxisLabel(value = 0, label = ft.Text("0", size = 10)), # Máxima Potência para dps
            ft.ChartAxisLabel(value = self.getMaxXPIV(), label = ft.Text(f"{self.getMaxXPIV()}V", size = 10)),
        ]
    
    def getMinYPIV(self):
        return 0

    def getMinXPIV(self):
        return 0

    def getMaxYPIV(self):
        return (math.ceil(self.Is/10)*10)+5
    
    def getMaxXPIV(self):
        return (math.ceil(self.vLim/10)*10)+5

    def generateVoltage(self):
        labels = []
        for i in range(0, len(self.timer)):
            labels.append(
                ft.LineChartDataPoint(self.timer[i], self.Voltage[i])
            )
        return labels

    def generateCurrent(self):
        labels = []
        c = (max(self.Voltage))/max(self.Current)
        for i in range(0, len(self.timer)):
            labels.append(
                ft.LineChartDataPoint(self.timer[i], c*self.Current[i])
            )
        return labels

    def generateP1(self):
        labels = []
        c = (max(self.Voltage))/max(self.Current)
        for i in range(0, len(self.timer)):
            labels.append(
                ft.LineChartDataPoint(self.timer[i], self.P1[i])
            )
        return labels

    def generateP2(self):
        labels = []
        c = (max(self.Voltage))/max(self.Current)
        for i in range(0, len(self.timer)):
            labels.append(
                ft.LineChartDataPoint(self.timer[i], self.P2[i])
            )
        return labels

    def generateP3(self):
        labels = []
        c = (max(self.Voltage))/max(self.Current)
        for i in range(0, len(self.timer)):
            labels.append(
                ft.LineChartDataPoint(self.timer[i], self.P3[i])
            )
        return labels

def main(page: ft.Page):
    page.title = "Software - TESF"
    page.vertical_alignment = ft.MainAxisAlignment.SPACE_EVENLY
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.resizable = False
    page.window.maximized = True

    titleP = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.CENTER,
        weight = ft.FontWeight.BOLD,
    )

    viewP = ft.LineChart(
        data_series = [
            ft.LineChartData(
                data_points = [],
                stroke_width=1,
                color=ft.colors.BLUE,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = [],
                stroke_width=1,
                color=ft.colors.GREEN,
                stroke_cap_round=True,
            )
        ],
        width = page.width*0.24,
        height = page.height*0.2,
        expand = True, 
        interactive = False 
    )
    
    titleVoltage = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.CENTER,
        weight = ft.FontWeight.BOLD,
    )

    viewVoltage = ft.LineChart(
        data_series = [
            ft.LineChartData(
                data_points = [],
                stroke_width=1,
                color=ft.colors.BLUE,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = [],
                stroke_width=1,
                color=ft.colors.RED,
                stroke_cap_round=True,
            )
        ],
        width = page.width*0.24,
        height = page.height*0.2,
        expand = True, 
        interactive = False 
    )

    titlePIV = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.CENTER,
        weight = ft.FontWeight.BOLD,
    )

    viewPIV = ft.LineChart(
        data_series = [
            ft.LineChartData(
                data_points = [],
                stroke_width=1,
                color=ft.colors.BLUE_ACCENT,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = [],
                stroke_width=1,
                color=ft.colors.GREEN_ACCENT,
                stroke_cap_round=True,
            )
        ],
        left_axis = ft.ChartAxis(
            labels = [],
            labels_size = 0,
        ),
        bottom_axis = ft.ChartAxis(
            labels = [],
            labels_size = 0,
        ),
        min_y = 0,
        min_x = 0,
        max_y = 0,
        max_x = 0,
        width = page.width*0.24,
        height = page.height*0.2,
        expand = True, 
        interactive = False
    )

    def restartHour(e):
        print(inputHour.value)
        p = PhotovoltaicCell(g.getTable(), inputHour.value)
        p.getValues()
        viewPIV.data_series = [
            ft.LineChartData(
                data_points = p.generateIV(),
                stroke_width=1,
                color=ft.colors.BLUE_ACCENT,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = p.generatePIV(),
                stroke_width=1,
                color=ft.colors.GREEN_ACCENT,
                stroke_cap_round=True,
            )
        ]
        viewPIV.left_axis.labels = p.getLeftAxisPIV()
        viewPIV.left_axis.labels_size = 40
        viewPIV.bottom_axis.labels = p.getBottomAxisPIV()
        viewPIV.bottom_axis.labels_size = 30
        viewPIV.min_y = p.getMinYPIV()
        viewPIV.min_x = p.getMinXPIV()
        viewPIV.max_y = p.getMaxYPIV()
        viewPIV.max_x = p.getMaxXPIV()

        viewVoltage.data_series = [
            ft.LineChartData(
                data_points = p.generateVoltage(),
                stroke_width=1,
                color=ft.colors.BLUE,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = p.generateCurrent(),
                stroke_width=1,
                color=ft.colors.RED,
                stroke_cap_round=True,
            )
        ]

        viewP.data_series = [
            ft.LineChartData(
                data_points = p.generateP1(),
                stroke_width=1,
                color=ft.colors.BLUE,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = p.generateP2(),
                stroke_width=1,
                color=ft.colors.RED,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = p.generateP3(),
                stroke_width=1,
                color=ft.colors.GREEN,
                stroke_cap_round=True,
            )
        ]

        inf01.value = "Irradiância Máxima: " + str(g.getMaxRadiance())
        inf02.value = "Temperatura Máxima: " + str(g.getMaxTemperature())

        titleINF01.value = "Ao longo do dia"
        inf01.value = "Irradiância Máxima: " + str(g.getMaxRadiance())
        inf02.value = "Temperatura Máxima: " + str(g.getMaxTemperature())

        curva01.value = "Is: " + str(max(p.I))
        curva02.value = "VoC: " + str(max(p.V))
        I, V = p.getId()
        curva03.value = "I de Potência Máxima: " + str(I)
        curva04.value = "V de Potência Máxima: " + str(V)
        curva05.value = "Potência Máxima: " + str(max(p.pot))

        page.update()

    inputHour = ft.Dropdown(
        bgcolor = ft.colors.TRANSPARENT,
        color = ft.colors.TRANSPARENT,
        disabled = True,
        opacity = 0,
        value = "",
        options = [],
        on_change = restartHour,
    )

    viewRadiance = ft.LineChart(
        data_series = [
            ft.LineChartData(
                data_points = [],
                stroke_width=1,
                color=ft.colors.YELLOW_ACCENT,
                stroke_cap_round=True,
            ),
        ],
        left_axis = ft.ChartAxis(
            labels = [],
            labels_size = 0,
        ),
        bottom_axis = ft.ChartAxis(
            labels = [],
            labels_size = 0,
        ),
        min_y = 0,
        min_x = 0,
        max_y = 0,
        max_x = 0,
        tooltip_bgcolor = ft.colors.with_opacity(0.8, ft.colors.BLACK),
        expand = True,
    )

    titleRadiance = ft.Text(
        value = "", 
        size = 20,
        text_align = ft.TextAlign.CENTER,
        weight = ft.FontWeight.BOLD,
    )

    viewTemperature = ft.LineChart(
        data_series = [
            ft.LineChartData(
                data_points = [],
                stroke_width=1,
                color=ft.colors.RED,
                stroke_cap_round=True,
            ),
        ],
        left_axis = ft.ChartAxis(
            labels = [],
            labels_size = 0,
        ),
        bottom_axis = ft.ChartAxis(
            labels = [],
            labels_size = 0,
        ),
        min_y = 0,
        min_x = 0,
        max_y = 0,
        max_x = 0,
        tooltip_bgcolor = ft.colors.with_opacity(0.8, ft.colors.BLACK),
        expand = True,
    )

    titleTemperature = ft.Text(
        value = "", 
        size = 20,
        text_align = ft.TextAlign.CENTER,
        weight = ft.FontWeight.BOLD,
    )

    titleINF01 = ft.Text(
        value = "", 
        size = 20,
        text_align = ft.TextAlign.CENTER,
        weight = ft.FontWeight.BOLD,
    )

    inf01 = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.LEFT,
    )

    inf02 = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.LEFT,
    )

    curva01 = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.LEFT,
    )

    curva02 = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.LEFT,
    )

    curva03 = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.LEFT,
    )

    curva04 = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.LEFT,
    )

    curva05 = ft.Text(
        value = "", 
        size = 15,
        text_align = ft.TextAlign.LEFT,
    )

    GraphicSpace =  ft.Row(
            controls = [
                ft.Container(
                        content = ft.Row(
                            controls = [
                                ft.Container(
                                    content = ft.Column(
                                        controls = [
                                            ft.Container(
                                                content = titleRadiance,
                                                width = page.width*0.7,
                                                height = page.height*0.055,
                                            ),
                                            viewRadiance,
                                            ft.Container(
                                                content = titleTemperature,
                                                width = page.width*0.7,
                                                height = page.height*0.055,
                                            ),
                                            viewTemperature
                                        ],
                                    ),
                                    width = page.width*0.7,
                                    height = page.height*0.9,
                                ),
                                ft.Container(
                                    content = ft.Column(
                                        controls = [
                                            inputHour,
                                            ft.Container(
                                                content = titlePIV,
                                                width = page.width*0.24,
                                            ),
                                            viewPIV,
                                            ft.Container(
                                                content = titleVoltage,
                                                width = page.width*0.24,
                                            ),
                                            viewVoltage,
                                            ft.Container(
                                                content = titleP,
                                                width = page.width*0.24,
                                            ),
                                            viewP,
                                        ],
                                    ),
                                    width = page.width*0.24,
                                    height = page.height*0.9,
                                )
                            ]
                        ),

                        width = page.width*0.95,
                        height = page.height*0.9,
                ),
                ft.Container(
                        content = ft.Row(
                            controls = [
                                ft.Container(
                                    content = ft.Column(
                                        controls = [
                                            ft.Container(
                                                content = titleRadiance,
                                                width = page.width*0.24,
                                                height = page.height*0.06,
                                            ),
                                            ft.Container(
                                                content = inf01,
                                                width = page.width*0.24,
                                                height = page.height*0.04,
                                            ),
                                            ft.Container(
                                                content = inf02,
                                                width = page.width*0.24,
                                                height = page.height*0.04,
                                            ),
                                            ft.Container(
                                                content = titleTemperature,
                                                width = page.width*0.24,
                                                height = page.height*0.06,
                                            ),
                                            ft.Container(
                                                content = curva01,
                                                width = page.width*0.24,
                                                height = page.height*0.04,
                                            ),
                                            ft.Container(
                                                content = curva02,
                                                width = page.width*0.24,
                                                height = page.height*0.04,
                                            ),
                                            ft.Container(
                                                content = curva03,
                                                width = page.width*0.24,
                                                height = page.height*0.04,
                                            ),
                                            ft.Container(
                                                content = curva04,
                                                width = page.width*0.24,
                                                height = page.height*0.04,
                                            ),
                                            ft.Container(
                                                content = curva05,
                                                width = page.width*0.24,
                                                height = page.height*0.04,
                                            ),
                                        ],
                                    ),
                                    width = page.width*0.24,
                                    height = page.height*0.9,
                                ),

                            ]
                        ),
                    width = page.width*0.24,
                    height = page.height*0.9,
                )
            ],
            alignment= ft.MainAxisAlignment.CENTER,
            width = page.width*1.2,        
        )

    # Container Principal - Row Header - Container 02 - buttonSpaceRecord02
    buttonSpaceRecord02 = ft.ElevatedButton(
        'A',
        icon=ft.icons.ADD,
        # on_click= ,
        width = 100,
        style = ft.ButtonStyle(padding = 20)
    )

    # Container Principal - Row Header - Container 02 - titleSpaceRecord
    titleSpaceRecord = ft.Container(
        content = ft.Text(
            "Gerenciamento", 
            size = 20,
            text_align = ft.TextAlign.CENTER,
            weight = ft.FontWeight.BOLD,
        ),
        width = page.width*0.595,
        height = page.height*0.055,
    )

    def dashboard(e):
        g.setPath("TabelaTESF.xlsx")

        titleTemperature.value = "Temperatura ao longo do dia"

        viewTemperature.data_series = [
            ft.LineChartData(
                data_points = g.generateDataSeriesTemperature(),
                stroke_width=1,
                color=ft.colors.RED_ACCENT,
                stroke_cap_round=True,
            )
        ]
        viewTemperature.left_axis.labels= g.getLeftAxisTemperature()
        viewTemperature.left_axis.labels_size = 40
        viewTemperature.bottom_axis.labels = g.getBottomAxis()
        viewTemperature.bottom_axis.labels_size = 30
        viewTemperature.min_y = g.getMinYTemperature()
        viewTemperature.min_x = g.getMinX()
        viewTemperature.max_y = g.getMaxYTemperature()
        viewTemperature.max_x = g.getMaxX()

        titleRadiance.value = "Irradiância ao longo do dia"

        viewRadiance.data_series = [
            ft.LineChartData(
                data_points = g.generateDataSeriesRadiance(),
                stroke_width=1,
                color=ft.colors.YELLOW_ACCENT,
                stroke_cap_round=True,
            )
        ]
        viewRadiance.left_axis.labels= g.getLeftAxisRadiance()
        viewRadiance.left_axis.labels_size = 40
        viewRadiance.bottom_axis.labels = g.getBottomAxis()
        viewRadiance.bottom_axis.labels_size = 30
        viewRadiance.min_y = g.getMinYRadiance()
        viewRadiance.min_x = g.getMinX()
        viewRadiance.max_y = g.getMaxYRadiance()
        viewRadiance.max_x = g.getMaxX()

        inputHour.value = "12:00"
        inputHour.options = g.getListHours()
        inputHour.bgcolor = ft.colors.BLACK
        inputHour.color = ft.colors.WHITE
        inputHour.disabled = False
        inputHour.opacity = 1

        titlePIV.value = "Curva V - I"

        p = PhotovoltaicCell(g.getTable(), inputHour.value)
        p.getValues()
        viewPIV.data_series = [
            ft.LineChartData(
                data_points = p.generateIV(),
                stroke_width=1,
                color=ft.colors.BLUE_ACCENT,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = p.generatePIV(),
                stroke_width=1,
                color=ft.colors.GREEN_ACCENT,
                stroke_cap_round=True,
            )
        ]
        viewPIV.left_axis.labels = p.getLeftAxisPIV()
        viewPIV.left_axis.labels_size = 40
        viewPIV.bottom_axis.labels = p.getBottomAxisPIV()
        viewPIV.bottom_axis.labels_size = 30
        viewPIV.min_y = p.getMinYPIV()
        viewPIV.min_x = p.getMinXPIV()
        viewPIV.max_y = p.getMaxYPIV()
        viewPIV.max_x = p.getMaxXPIV()

        titleVoltage.value = "Tensão e Corrente"

        viewVoltage.data_series = [
            ft.LineChartData(
                data_points = p.generateVoltage(),
                stroke_width=1,
                color=ft.colors.BLUE,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = p.generateCurrent(),
                stroke_width=1,
                color=ft.colors.RED,
                stroke_cap_round=True,
            )
        ]


        titleP.value = "Potências"

        viewP.data_series = [
            ft.LineChartData(
                data_points = p.generateP1(),
                stroke_width=1,
                color=ft.colors.BLUE,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = p.generateP2(),
                stroke_width=1,
                color=ft.colors.RED,
                stroke_cap_round=True,
            ),
            ft.LineChartData(
                data_points = p.generateP3(),
                stroke_width=1,
                color=ft.colors.GREEN,
                stroke_cap_round=True,
            )
        ]




        titleINF01.value = "Ao longo do dia"
        inf01.value = "Irradiância Máxima: " + str(g.getMaxRadiance())
        inf02.value = "Temperatura Máxima: " + str(g.getMaxTemperature())

        curva01.value = "Is: " + str(max(p.I))
        curva02.value = "VoC: " + str(max(p.V))
        I, V = p.getId()
        curva03.value = "I de Potência Máxima: " + str(I)
        curva04.value = "V de Potência Máxima: " + str(V)
        curva05.value = "Potência Máxima: " + str(max(p.pot))

        

        page.update()

    # Container Principal - Row Header - Container 01 - buttonActionSpaceFile
    buttonActionSpaceFile = ft.ElevatedButton(
        'Gerar Dashboard',
        icon=ft.icons.DASHBOARD_CUSTOMIZE,
        on_click = dashboard,
        width = 300,
        style = ft.ButtonStyle(padding = 20)
    )

    # Container Principal - Row Header - Container 01 - buttonSpaceFile - def filesResult
    def filesResult(event: ft.FilePickerResultEvent):
        if event.files:
            path = ', '.join(f.path for f in event.files)
        else:
            page.open(ft.AlertDialog(title=ft.Text("Erro ao Carregar arquivo, tente novamente!")))
            path = ""
        g.setPath()

    # Container Principal - Row Header - Container 01 - buttonSpaceFile - filesDialog
    filesDialog = ft.FilePicker(on_result=filesResult)

    # Container Principal - Row Header - Container 01 - buttonSpaceFile
    buttonSpaceFile = ft.ElevatedButton(
        'Adicionar Planilha',
        icon=ft.icons.UPLOAD_FILE,
        on_click=lambda _: filesDialog.pick_files(allow_multiple=True),
        width = 300,
        style = ft.ButtonStyle(padding = 20)
    )

    # Container Principal - Row Header - Container 01 - titleSpaceFile
    titleSpaceFile = ft.Container(
        content = ft.Text(
            "Gerenciamento de Arquivos", 
            size = 20,
            text_align = ft.TextAlign.CENTER,
            weight = ft.FontWeight.BOLD,
        ),
        width = page.width*0.9,
        height = page.height*0.055,
    )

    # Container Principal - Row Header
    headerSpace =  ft.Row(
            controls = [
                ft.Container(
                    content = ft.Row(
                        controls = [titleSpaceFile, buttonSpaceFile, buttonActionSpaceFile],
                        alignment = ft.MainAxisAlignment.SPACE_EVENLY,
                        vertical_alignment = ft.CrossAxisAlignment.CENTER,
                        width = page.width*0.95,
                        height = page.height*0.165,
                        wrap = True,
                    ),
                ),
                ft.Container(
                    content = ft.Row(
                        controls=[titleSpaceRecord, buttonSpaceRecord02],
                        alignment = ft.MainAxisAlignment.SPACE_EVENLY,
                        vertical_alignment = ft.CrossAxisAlignment.CENTER,
                        width = page.width*0.24,
                        height = page.height*0.165,
                        wrap = True,
                    ),
                    disabled = True,
                    opacity = 0
                ),
            ],
            alignment= ft.MainAxisAlignment.CENTER,
            width = page.width*1.2,        
        )

    # Container Principal
    viewControl = ft.Container(
        content = ft.Column(
            controls = [
                headerSpace,
                GraphicSpace,
            ],
            alignment = ft.MainAxisAlignment.CENTER,
            horizontal_alignment = ft.CrossAxisAlignment.CENTER,
            width = page.width*1.2,
            height = page.height*1.1, 
        ),
    )

    page.overlay.extend([filesDialog])
    page.add(viewControl)

ft.app(target=main)
