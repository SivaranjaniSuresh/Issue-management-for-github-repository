from pymilvus import connections, Collection
# Connect to Milvus
connections.connect(alias="default", host="34.138.127.169", port="19530") 
# Set collection name and search parameters
collection_name = "my_collection"
collection = Collection(name=collection_name) 
# Replace this with the vector you want to search for
search_vector = [-0.448660284280777, -0.28080201148986816, -0.10345474630594254, 0.33812594413757324, 0.16459788382053375, -0.05959273874759674, 0.10910109430551529, 0.12390085309743881, 0.12366292625665665, -0.992030918598175, -0.008630474098026752, 0.16479294002056122, 0.9201486110687256, -0.14717359840869904, 0.8048827052116394, -0.22650717198848724, 0.37639617919921875, -0.2675168812274933, 0.19354157149791718, 0.25574004650115967, 0.7122358679771423, 0.5126399397850037, 0.3412504196166992, 0.230244442820549, 0.31965431571006775, 0.15965725481510162, -0.17873980104923248, 0.8444700241088867, 0.7859134674072266, 0.8169963955879211, -0.2730121314525604, 0.17832063138484955, -0.9634387493133545, -0.19274865090847015, -0.3248012959957123, -0.9301568865776062, 0.12219872325658798, -0.40355587005615234, -0.21720464527606964, 0.08428584784269333, -0.8173756003379822, 0.24696211516857147, 0.9791646599769592, 0.29555705189704895, 0.4470544755458832, -0.09241461753845215, -0.762856662273407, 0.19115591049194336, -0.7258415222167969, -0.013609807007014751, 0.09697726368904114, 0.1703600138425827, 0.08080584555864334, 0.17499999701976776, 0.20856748521327972, -0.18003706634044647, -0.01792246662080288, 0.15094949305057526, -0.1102256253361702, -0.2927822172641754, -0.3588825762271881, 0.42291584610939026, -0.16632407903671265, -0.6412460803985596, -0.04704894497990608, -0.0969633087515831, -0.23173338174819946, -0.3359001576900482, 0.021276317536830902, 0.028518930077552795, 0.21258138120174408, 0.103919617831707, -0.021861335262656212, -0.7632410526275635, -0.21487826108932495, 0.19427497684955597, -0.412766695022583, 0.9063604474067688, 0.09359758347272873, -0.9479832649230957, 0.26683640480041504, -0.22137264907360077, 0.3476286232471466, 0.49113431572914124, -0.30634960532188416, -0.8591297268867493, 0.28925788402557373, -0.1314171403646469, -0.9585993885993958, 0.23097403347492218, 0.42422571778297424, -0.04386362060904503, 0.24948954582214355, 0.3085116446018219, 0.0014143586158752441, -0.3886221945285797, -0.1224723532795906, -0.24938417971134186, -0.2959965765476227, -0.40363970398902893, 0.23312558233737946, -0.14543430507183075, -0.1322992593050003, -0.1834937483072281, 0.2704879939556122, -0.154417484998703, -0.11247126013040543, 0.1443704217672348, -0.31671246886253357, 0.4189964234828949, 0.3551003932952881, -0.26289311051368713, 0.18011999130249023, -0.7508710026741028, 0.2556096017360687, -0.22135882079601288, -0.9375014305114746, -0.32270100712776184, -0.970469057559967, 0.611483097076416, -0.162599578499794, -0.2412467747926712, 0.7641394734382629, -0.1993045061826706, 0.12320151925086975, -0.0602310486137867, 0.09931027889251709, -0.8736054301261902, -0.05346808210015297, -0.4336968660354614, 0.28293418884277344, -0.17014312744140625, -0.9105441570281982, -0.9174095988273621, 0.36941492557525635, 0.8183786273002625, 0.07262928038835526, 0.9748069643974304, -0.13641591370105743, 0.8658668398857117, 0.5710983276367188, -0.11177065223455429, -0.305401474237442, -0.35388174653053284, 0.45324692130088806, -0.23937876522541046, -0.3408208191394806, 0.057879310101270676, -0.11125732213258743, -0.36894282698631287, -0.24040627479553223, -0.16020001471042633, 0.11811729520559311, -0.7544102668762207, -0.19138586521148682, 0.8405938148498535, 0.17477171123027802, 0.17340345680713654, 0.5618740916252136, -0.0871562734246254, -0.052549902349710464, 0.5783223509788513, 0.3358859717845917, 0.2699074447154999, 0.14074744284152985, 0.2902280390262604, -0.47700437903404236, 0.28710708022117615, -0.6464786529541016, 0.37851205468177795, 0.09069233387708664, -0.13932526111602783, -0.13490834832191467, -0.9545952677726746, -0.24262605607509613, 0.16916675865650177, 0.9475815892219543, 0.36033400893211365, 0.24157769978046417, -0.17829196155071259, -0.2602440416812897, 0.09389660507440567, -0.8842918872833252, 0.9336610436439514, -0.06043514236807823, 0.20674443244934082, -0.45850786566734314, 2.9802322387695312e-05, -0.647430956363678, -0.02377154491841793, 0.3953549563884735, -0.006486078258603811, -0.7008390426635742, -0.10878535360097885, -0.40295934677124023, -0.16509854793548584, -0.33724746108055115, 0.13807959854602814, -0.31219857931137085, -0.3196290135383606, -0.2517942488193512, 0.8638968467712402, 0.13877266645431519, 0.3514491319656372, -0.08490429073572159, 0.26601529121398926, -0.736191987991333, -0.5312474966049194, 0.01377064734697342, 0.13938124477863312, 0.08816776424646378, 0.9330738186836243, -0.3895643651485443, 0.08051123470067978, -0.5759561657905579, -0.9280886650085449, 0.03932000324130058, -0.5525170564651489, -0.006412062793970108, -0.41758593916893005, 0.33746612071990967, -0.1776503324508667, -0.6298379302024841, 0.2566640377044678, -0.31210097670555115, -0.6230829358100891, 0.22524982690811157, -0.3221047520637512, 0.19338096678256989, -0.2758620083332062, 0.8368337750434875, 0.266767293214798, -0.5591201186180115, -0.2380809783935547, 0.9456636309623718, -0.1464850753545761, -0.7669458985328674, 0.47472384572029114, -0.1549176424741745, 0.359301894903183, -0.39967814087867737, 0.8743085861206055, 0.18066489696502686, 0.20182310044765472, -0.7103957533836365, -0.06823861598968506, -0.1599736213684082, 0.5297349095344543, -0.12558776140213013, -0.48732301592826843, -0.3802962005138397, 0.3369828164577484, 0.13610175251960754, 0.4572887718677521, -0.025223316624760628, -0.07708770781755447, -0.790055513381958, -0.9033779501914978, -0.6533058285713196, 0.36704444885253906, -0.9723955988883972, 0.24677348136901855, 0.21620887517929077, 0.3077416718006134, -0.28300371766090393, -0.017434636130928993, -0.9024466872215271, 0.21489214897155762, 0.09475639462471008, 0.49270787835121155, -0.305436372756958, -0.32750675082206726, -0.002448057057335973, -0.9223478436470032, 0.1938173770904541, -0.07312104105949402, 0.4088165760040283, 0.03318999335169792, -0.7816428542137146, 0.3659399747848511, 0.5309381484985352, 0.23902703821659088, 0.12382920831441879, 0.592161238193512, 0.5500795841217041, 0.90091872215271, 0.7393204569816589, -0.02870846726000309, -0.5293328166007996, -0.4064722955226898, 0.9953134059906006, -0.3953787386417389, -0.7570760846138, -0.7556171417236328, -0.2236158698797226, 0.4796418249607086, -0.8769042491912842, -0.08194605261087418, -0.08798976987600327, -0.7543660998344421, -0.15683495998382568, 0.8496058583259583, 0.3928752839565277, -0.8331827521324158, 0.462700217962265, 0.689532458782196, -0.3872039020061493, 0.006172865629196167, -0.40582844614982605, 0.90120929479599, -0.13050933182239532, 0.5234513878822327, -0.13839945197105408, 0.3330155611038208, -0.2278171181678772, -0.5658167004585266, 0.12404245883226395, -0.1040518581867218, 0.40340566635131836, 0.09826875478029251, -0.45553550124168396, -0.706494152545929, 0.2938227951526642, -0.05839425325393677, -0.01648729108273983, -0.8832013010978699, -0.18619346618652344, -0.4869225323200226, 0.40110158920288086, 0.14882542192935944, 0.178493931889534, -0.31581178307533264, 0.11480536311864853, 0.03607408329844475, 0.1416289061307907, 0.31569984555244446, -0.7111130356788635, -0.17551414668560028, -0.39732030034065247, -0.3387446701526642, 0.20074458420276642, -0.9489085674285889, 0.872018575668335, -0.15350207686424255, -0.08514505624771118, 0.8331773281097412, 0.3951718509197235, -0.6678746342658997, 0.12423750758171082, 0.01652686297893524, -0.6440967917442322, 0.8597805500030518, 0.4430231750011444, -0.9501373767852783, -0.30141007900238037, 0.057135820388793945, -0.2455664873123169, -0.4499794542789459, 0.9759463667869568, -0.08835119009017944, 0.11136306077241898, 0.09937798231840134, 0.9730327129364014, -0.9639996886253357, 0.34545084834098816, -0.4748792350292206, -0.8609870076179504, 0.7887380719184875, 0.8611466884613037, -0.00969503354281187, -0.5642555356025696, -0.010592189617455006, 0.16648422181606293, 0.22096925973892212, -0.307880163192749, 0.06334885209798813, 0.36822548508644104, -0.08276925981044769, 0.8074859976768494, 0.19772034883499146, -0.2955159842967987, 0.2759411633014679, 0.14217165112495422, 0.37398478388786316, 0.299887478351593, 0.29272541403770447, -0.16283410787582397, -0.012155008502304554, -0.2335374802350998, -0.6447683572769165, -0.7189351916313171, 0.3764001131057739, 0.8397972583770752, 0.009588971734046936, 0.3374082148075104, 0.6507964730262756, -0.1483350247144699, 0.10059081763029099, 0.15008141100406647, 0.24537062644958496, -0.14096160233020782, -0.5488787293434143, 0.22480164468288422, -0.295221209526062, -0.9781783223152161, 0.4397796094417572, 0.17679236829280853, -0.11793521791696548, 0.7830764651298523, -0.04382966086268425, 0.14349842071533203, -0.15262848138809204, 0.09626344591379166, 0.2441471815109253, -0.17077893018722534, -0.23702387511730194, 0.9276185035705566, -0.09289771318435669, 0.32803210616111755, 0.23866581916809082, 0.16182374954223633, -0.31260326504707336, -0.31086045503616333, 0.021405009552836418, -0.9299328923225403, -0.0870044007897377, -0.829542875289917, 0.8884862065315247, 0.04312802478671074, 0.17062318325042725, 0.21695809066295624, 0.35673460364341736, 0.7503895163536072, -0.6347836852073669, 0.35553669929504395, 0.5702246427536011, 0.28971320390701294, -0.4829173982143402, -0.2958272695541382, -0.2648426592350006, 0.02571624517440796, 0.14089876413345337, -0.11214498430490494, 0.09939368814229965, -0.8566321730613708, -0.22510503232479095, -0.04590439796447754, -0.3877737820148468, -0.8807356953620911, 0.003470818279311061, -0.2507570683956146, 0.04455416277050972, -0.43153342604637146, -0.058052387088537216, -0.5231533646583557, -0.17033624649047852, -0.3297679126262665, -0.7798969149589539, 0.5963273048400879, -0.21131862699985504, 0.1672825962305069, -0.25835585594177246, 0.3903476893901825, -0.1293725222349167, 0.7209280133247375, -0.2811843454837799, -0.0764043927192688, -0.16911490261554718, -0.5422484874725342, 0.15314751863479614, -0.5098552703857422, -0.041924625635147095, -0.20994694530963898, 0.8614527583122253, -0.26855847239494324, 0.15005412697792053, 0.4632902443408966, 0.026145556941628456, -0.2752399444580078, 0.28170087933540344, 0.2870219647884369, 0.14755721390247345, 0.2187497764825821, 0.18149296939373016, 0.5213640928268433, -0.18796004354953766, 0.40615615248680115, 0.25835320353507996, -0.07279949635267258, 0.717902660369873, 0.13729554414749146, 0.10418031364679337, -0.041131142526865005, 0.16702775657176971, 0.13099417090415955, -0.11115294694900513, -0.25252917408943176, -0.35776257514953613, -0.2517979145050049, -0.234386146068573, 0.3359801471233368, 0.6378015279769897, 0.17711935937404633, 0.25666284561157227, -0.9579278826713562, -0.12068292498588562, -0.5069226026535034, 0.5647510886192322, 0.7531483173370361, -0.26142624020576477, 0.34893786907196045, 0.253257155418396, -0.18953363597393036, -0.19602255523204803, -0.19915658235549927, -0.10351765155792236, 0.006214343477040529, 0.14111338555812836, 0.8545724749565125, -0.40845629572868347, -0.934722363948822, -0.6193310618400574, 0.17708231508731842, -0.8663633465766907, 0.48936429619789124, -0.3906780183315277, -0.12098833173513412, -0.06302273273468018, 0.09729015082120895, -0.4809606373310089, 0.05499076843261719, -0.8879665732383728, -0.24576382339000702, 0.054382193833589554, 0.914766252040863, 0.29305100440979004, -0.3545961081981659, -0.7058963775634766, 0.0367162711918354, 0.09138715267181396, 0.13363680243492126, -0.7745547294616699, 0.8986613750457764, -0.7237256169319153, 0.059005606919527054, 0.8301472663879395, 0.3786686360836029, -0.21194620430469513, 0.07748329639434814, -0.28887471556663513, 0.07832373678684235, -0.1393144577741623, 0.24472516775131226, -0.8272692561149597, -0.21347570419311523, -0.16823576390743256, 0.1562473028898239, -0.10371318459510803, -0.3810006380081177, 0.381563663482666, 0.24541141092777252, -0.25140485167503357, -0.25853073596954346, -0.12067877501249313, 0.1449887603521347, 0.37775328755378723, -0.14018401503562927, -0.06856489181518555, 0.05903084948658943, -0.06393019109964371, -0.8197152614593506, -0.23039382696151733, -0.11139926314353943, -0.5554988384246826, 0.3527628481388092, -0.8549143671989441, 0.11712747067213058, -0.44301557540893555, -0.12272240966558456, 0.7933687567710876, 0.3056807219982147, 0.1777067631483078, -0.5473611950874329, 0.2687920033931732, 0.6374031901359558, 0.6560924649238586, -0.1541907638311386, 0.4460982382297516, -0.6440622806549072, 0.18487508594989777, -0.22277142107486725, 0.18913428485393524, -0.09818776696920395, 0.5788000822067261, -0.11010736972093582, 0.8698320984840393, 0.10171728581190109, -0.2648453414440155, -0.3259866535663605, 0.19545789062976837, -0.13355860114097595, 0.5447127819061279, 0.028840214014053345, -0.8764109015464783, 0.1866713911294937, -0.3236541152000427, -0.6208197474479675, 0.23293377459049225, 0.15682436525821686, -0.4210536479949951, -0.26477742195129395, 0.7448136210441589, 0.13529153168201447, -0.3187018930912018, 0.18187178671360016, -0.18434447050094604, -0.23168309032917023, 0.12645567953586578, 0.10707303136587143, 0.9510111212730408, 0.3173862099647522, 0.44098806381225586, -0.048045605421066284, -0.14518176019191742, 0.9037986397743225, 0.3277738094329834, -0.04023342207074165, 0.10528726130723953, 0.8164928555488586, 0.3615492582321167, -0.8663628101348877, -0.28241053223609924, -0.7611469626426697, -0.1744479089975357, -0.7476921081542969, 0.16062338650226593, 0.3053511083126068, 0.7808218002319336, -0.1998734027147293, 0.8586803078651428, 0.08558716624975204, -0.024440303444862366, 0.0036290783900767565, 0.11563044041395187, 0.08809473365545273, -0.7678170800209045, -0.9493909478187561, -0.9565768837928772, 0.19668275117874146, -0.26656559109687805, -0.08289352059364319, 0.28192612528800964, 0.22541451454162598, 0.20334547758102417, 0.11589968204498291, -0.6553196907043457, 0.8168554902076721, 0.3258662521839142, -0.04038190841674805, 0.8830187916755676, 0.02222585678100586, 0.41541942954063416, 0.1594230979681015, -0.9260311722755432, -0.1980876922607422, -0.249454066157341, -0.234876349568367, 0.5371890068054199, 0.3234610855579376, 0.6461005806922913, 0.15750594437122345, -0.3154553771018982, -0.3364553451538086, -0.08296891301870346, -0.5640817880630493, -0.9536049962043762, 0.3353421688079834, 0.3278305232524872, -0.029627859592437744, 0.9092792868614197, -0.3580251932144165, -0.12253352254629135, 0.3837045729160309, -0.2549358010292053, -0.009249965660274029, 0.46811535954475403, 0.2100115418434143, -0.07370772212743759, 0.7003867030143738, 0.7588353157043457, 0.4901549518108368, 0.940204918384552, -0.00954227615147829, 0.11985728144645691, 0.18023772537708282, 0.2645796239376068, 0.7877941131591797, -0.8575003147125244, 0.18487995862960815, 0.3894631564617157, -0.10236092656850815, 0.25267091393470764, -0.3038872480392456, -0.19894124567508698, 0.7388353943824768, -0.32326242327690125, 0.3519774377346039, -0.34856536984443665, 0.013404503464698792, -0.2237439751625061, -0.16585056483745575, -0.4138113558292389, -0.06794476509094238, 0.28342798352241516, 0.0856228768825531, 0.8396430611610413, 0.2946493625640869, -0.10189724713563919, -0.2615971267223358, -0.06126788258552551, 0.27355507016181946, -0.8584328293800354, 0.07283594459295273, 0.0013047618558630347, 0.42835554480552673, 0.35489925742149353, 0.07917126268148422, 0.7799912095069885, -0.28052252531051636, -0.154866561293602, 0.036615826189517975, -0.48685625195503235, 0.35425302386283875, -0.20898611843585968, -0.3886094093322754, -0.2975594103336334, 0.32505354285240173, 0.21986842155456543, 0.5360642075538635, 0.11942023038864136, 0.3227570652961731, -0.2988763749599457, -0.17086981236934662, 0.24964118003845215, -0.25442057847976685, -0.6359962224960327, 0.18609939515590668, 0.14455480873584747, -0.07198797911405563, -0.02274709939956665, 0.14752905070781708, 0.09990226477384567, -0.697417676448822, -0.33869680762290955, 0.5421030521392822, 0.11268270760774612, -0.17123113572597504, -0.09730184078216553, 0.2503412663936615, 0.39279165863990784, 0.11878519505262375, 0.6069816946983337, 0.05615606531500816, 0.5025558471679688, 0.33899345993995667, -0.30597007274627686, -0.5155597925186157, 0.610741913318634]
# Set the number of results you want to retrieve
top_k = 999
# The name of the vector field in your collection
anns_field = "embeddings"
# Set search parameters
search_params = { "metric_type": "L2", # Distance metric (e.g., L2, IP, etc.) 
                  "params": {"nprobe": 9999}, # Search parameter, nprobe is the number of buckets to search
                } 
# Perform the search
results = collection.search(data=[search_vector], anns_field=anns_field, param=search_params, limit=top_k) 
# Print the top nearest results
print("Top nearest results:") 
for result in results: 
    for match in result: 
        print(f"ID: {match.id}, Distance: {match.distance}")